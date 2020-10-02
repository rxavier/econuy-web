import re
import uuid
from PIL import Image
from os import path, mkdir
from io import BytesIO
from typing import List, Dict

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash
from dash.dependencies import Input, Output, State, ALL, MATCH
from dash.exceptions import PreventUpdate
from dash_table.Format import Format, Scheme, Group
from flask import (url_for, send_file, request, flash,
                   current_app, send_from_directory)
from sqlalchemy.exc import ProgrammingError

from econuy import transform
from econuy_web.app_strings import table_options
from econuy.utils import sqlutil, metadata

external_stylesheets = [dbc.themes.FLATLY]

url_base = "/dash/viz/"


def add_dash(server):
    app = Dash(server=server, url_base_pathname=url_base,
               external_stylesheets=external_stylesheets)
    app.layout = html.Div([html.H1("Visualización interactiva"),
                           dbc.Button("Agregar conjunto de indicadores",
                                      id="add-indicator",
                                      n_clicks=0,
                                      color="primary"),
                           html.Br(), html.Br(),
                           html.Div(id="indicator-container",
                                    children=[]),
                           html.Br(),
                           html.Div(
                               id="chart-type-container",
                               children=[
                                   html.P("Tipo de visualización",
                                          style={"display": "inline-block"}),
                                   dbc.RadioItems(
                                       id="chart-type",
                                       options=[{"label": "Líneas",
                                                 "value": "line"},
                                                {"label": "Barras",
                                                 "value": "bar"},
                                                {"label": "Barras apiladas",
                                                 "value": "stackbar"},
                                                {"label": "Áreas",
                                                 "value": "area"},
                                                {"label": "Áreas normalizadas",
                                                 "value": "normarea"},
                                                {"label": "Tabla",
                                                 "value": "table"}],
                                       value="line",
                                       inline=True,
                                       style={"margin-left": "10px"})]),
                           html.Div(style={"height": "5px"}),
                           html.Div(id="date-range-container",
                                    children=[
                                        "Filtrar fechas",
                                        html.Div(
                                            dcc.DatePickerRange(
                                                id="date-picker",
                                                start_date_placeholder_text="Fecha inicial",
                                                end_date_placeholder_text="Fecha final",
                                                display_format="DD-MM-YYYY"),
                                            style={
                                                "display": "inline-block",
                                                "margin-left": "10px"})]),
                           html.Div(
                               [html.Br(),
                                dbc.Input(placeholder="Título del gráfico",
                                          type="text", id="title",
                                          debounce=True),
                                dbc.Input(placeholder="Subtítulo del gráfico",
                                          type="text", id="subtitle",
                                          debounce=True)],
                               id="title-subtitle"),
                           html.Br(),
                           dbc.Button("Actualizar consulta",
                                      id="submit",
                                      color="dark",
                                      style={
                                          "display": "inline-block",
                                          "margin": "10px"}),
                           html.Div([html.A(
                               dbc.Button("Exportar a Excel",
                                          id="download-button",
                                          color="dark"),
                               id="download-link",
                               style={"display": "none"}),
                               html.A(
                                   dbc.Button("Exportar a HTML",
                                              id="download-html-button",
                                              color="dark"),
                                   id="download-html-link",
                                   style={"display": "none"})]),
                           html.Div(
                               className="loader-wrapper",
                               children=[dcc.Loading(
                                   html.Div(id="viz-container", children=[])
                               )]
                           ),
                           html.Br(),
                           dbc.Button("Desplegar metadatos",
                                      id="metadata-button",
                                      style={"display": "none"},
                                      color="dark"),
                           html.Br(),
                           html.Div(id="metadata", children=[]),
                           dbc.Toast(children=[], id="update-toast",
                                     is_open=False, header="Información",
                                     style={"position": "fixed", "top": 5,
                                            "right": 5},
                                     duration=5000, icon="success",
                                     fade=True)])

    register_callbacks(app)

    return app.server


def register_callbacks(app):
    from econuy_web import db

    @app.callback(
        [Output("viz-container", "children"),
         Output("metadata-button", "style"),
         Output("metadata", "children"),
         Output("download-link", "href"),
         Output("download-link", "style"),
         Output("download-html-link", "href"),
         Output("download-html-link", "style"),
         Output("update-toast", "is_open"),
         Output("update-toast", "icon"),
         Output("update-toast", "children"),
         ],
        [Input("submit", "n_clicks")],
        [State("chart-type", "value"),
         State("title", "value"),
         State("subtitle", "value"),
         State({"type": "table-dropdown", "index": ALL}, "value"),
         State({"type": "indicator-dropdown", "index": ALL}, "value"),
         State({"type": "usd-check", "index": ALL}, "value"),
         State({"type": "real-check", "index": ALL}, "value"),
         State({"type": "real-range", "index": ALL}, "start_date"),
         State({"type": "real-range", "index": ALL}, "end_date"),
         State({"type": "gdp-check", "index": ALL}, "value"),
         State({"type": "resample-check", "index": ALL}, "value"),
         State({"type": "resample-frequency", "index": ALL}, "value"),
         State({"type": "resample-operation", "index": ALL}, "value"),
         State({"type": "rolling-check", "index": ALL}, "value"),
         State({"type": "rolling-periods", "index": ALL}, "value"),
         State({"type": "rolling-operation", "index": ALL}, "value"),
         State({"type": "base-check", "index": ALL}, "value"),
         State({"type": "base-range", "index": ALL}, "start_date"),
         State({"type": "base-range", "index": ALL}, "end_date"),
         State({"type": "base-base", "index": ALL}, "value"),
         State({"type": "chg-diff-check", "index": ALL}, "value"),
         State({"type": "chg-diff-operation", "index": ALL}, "value"),
         State({"type": "chg-diff-period", "index": ALL}, "value"),
         State({"type": "seas-check", "index": ALL}, "value"),
         State({"type": "seas-method", "index": ALL}, "value"),
         State({"type": "seas-type", "index": ALL}, "value"),
         State({"type": "order-1", "index": ALL}, "value"),
         State({"type": "order-2", "index": ALL}, "value"),
         State({"type": "order-3", "index": ALL}, "value"),
         State({"type": "order-4", "index": ALL}, "value"),
         State({"type": "order-5", "index": ALL}, "value"),
         State({"type": "order-6", "index": ALL}, "value"),
         State({"type": "order-7", "index": ALL}, "value"),
         State({"type": "order-8", "index": ALL}, "value"),
         State("date-picker", "start_date"),
         State("date-picker", "end_date"),
         State("viz-container", "children"),
         State("metadata-button", "style"),
         State("metadata", "children"),
         State("download-link", "href"),
         State("download-link", "style"),
         State("download-html-link", "href"),
         State("download-html-link", "style"),
         ])
    def update_df(submit,
                  chart_type, title, subtitle, table_s, indicator_s, usd_s,
                  real_s, real_start_s, real_end_s, gdp_s, resample_s,
                  resample_frequency_s, resample_operation_s, rolling_s,
                  rolling_period_s, rolling_operation_s, base_index_s,
                  base_start_s, base_end_s, base_base_s, chg_diff_s,
                  chg_diff_operation_s, chg_diff_period_s, seas_s,
                  seas_method_s, seas_type_s, orders_1_s, order_2_s, order_3_s,
                  order_4_s, order_5_s, order_6_s, order_7_s, order_8_s,
                  start_date, end_date, state_viz,
                  state_metadata_btn, state_metadata, state_href,
                  state_link_style, state_html_href, state_html_link_style):
        dataframes = []
        labels = []
        arr_orders_s = []
        trimmed_tables = []
        valid_tables = [x for x in table_s if x is not None]
        for (table,
             indicator,
             usd,
             real,
             real_start,
             real_end,
             gdp,
             resample,
             resample_frequency,
             resample_operation,
             rolling,
             rolling_periods,
             rolling_operations,
             base_index,
             base_start,
             base_end,
             base_base,
             chg_diff,
             chg_diff_operation,
             chg_diff_period,
             seas,
             seas_method,
             seas_type,
             order_1,
             order_2,
             order_3,
             order_4,
             order_5,
             order_6,
             order_7,
             order_8) in zip(table_s,
                             indicator_s,
                             usd_s,
                             real_s,
                             real_start_s,
                             real_end_s,
                             gdp_s,
                             resample_s,
                             resample_frequency_s,
                             resample_operation_s,
                             rolling_s,
                             rolling_period_s,
                             rolling_operation_s,
                             base_index_s,
                             base_start_s,
                             base_end_s,
                             base_base_s,
                             chg_diff_s,
                             chg_diff_operation_s,
                             chg_diff_period_s,
                             seas_s,
                             seas_method_s,
                             seas_type_s,
                             orders_1_s,
                             order_2_s,
                             order_3_s,
                             order_4_s,
                             order_5_s,
                             order_6_s,
                             order_7_s,
                             order_8_s):
            if ((True in resample and
                 (resample_frequency is None or resample_operation is None))
                    or (True in rolling and
                        (rolling_periods is None or
                         rolling_operations is None))
                    or (True in base_index
                        and (base_start is None or
                             base_base is None))
                    or (True in chg_diff and
                        (chg_diff_period is None or
                         chg_diff_operation is None))
                    or (True in seas and
                        (seas_method is None or
                         seas_type is None))):
                return (state_viz, state_metadata_btn,
                        state_metadata, state_href, state_link_style,
                        state_html_href, state_html_link_style, True,
                        "warning", html.P("Algunos parámetros obligatorios no "
                                          "establecidos. Visualización no "
                                          "actualizada", className="mb-0"))
            if table is None or indicator is None or indicator == []:
                continue
            if "*" in indicator:
                indicator = "*"
            df_aux = sqlutil.read(con=db.engine, table_name=table,
                                  cols=indicator)
            trimmed_table = re.sub(r" \(([^)]+)\)$", "", table_options[table])
            trimmed_tables.append(trimmed_table)
            if len(set(valid_tables)) > 1:
                table_text = f"{trimmed_table}_"
            else:
                table_text = ""
            df_aux.columns.set_levels(table_text
                                      + df_aux.columns.levels[0],
                                      level=0, inplace=True)
            orders = [order_1, order_2, order_3, order_4, order_5,
                      order_6, order_7, order_8]
            for i in range(len(orders)):
                if orders[i] is None:
                    orders[i] = 1
            submit_order = {k: v for k, v in
                            zip(["usd", "real", "gdp", "res", "roll",
                                 "base_index", "chg_diff", "seas"], orders)}
            all_transforms = {k: (True if True in v else False) for k, v
                              in
                              {"usd": usd, "real": real, "gdp": gdp,
                               "res": resample, "roll": rolling,
                               "base_index": base_index, "chg_diff": chg_diff,
                               "seas": seas}.items()}
            arr_orders = define_order(submit_order, all_transforms)
            arr_orders_s.append(arr_orders)
            function_dict = {
                "usd": lambda x: transform.convert_usd(x, update_loc=db.engine,
                                                       only_get=True),
                "real": lambda x: transform.convert_real(
                    x, update_loc=db.engine, only_get=True,
                    start_date=real_start,
                    end_date=real_end),
                "gdp": lambda x: transform.convert_gdp(x, update_loc=db.engine,
                                                       only_get=True),
                "res": lambda x: transform.resample(
                    x, target=resample_frequency, operation=resample_operation
                ),
                "roll": lambda x: transform.rolling(
                    x, periods=rolling_periods, operation=rolling_operations
                ),
                "base_index": lambda x: transform.base_index(
                    x, start_date=base_start,
                    end_date=base_end,
                    base=base_base),
                "chg_diff": lambda x: transform.chg_diff(
                    x, operation=chg_diff_operation,
                    period_op=chg_diff_period),
                "seas": lambda x: transform.decompose(x,
                                                      flavor=seas_type,
                                                      method=seas_method,
                                                      force_x13=True)
            }

            for t in arr_orders.values():
                df_aux = function_dict[t](df_aux)
            dataframes.append(df_aux)
            labels.extend(list(df_aux.columns.get_level_values(0)))

        if len(dataframes) == 0:
            return ([],
                    {"display": "none"}, [], "", {"display": "none"}, "",
                    {"display": "none"},
                    False, "primary", "")
        df = fix_freqs_and_names(dataframes)
        df = df.dropna(how="all", axis=0)
        if start_date is not None:
            if end_date is not None:
                df = df.loc[(df.index >= start_date) & (df.index <= end_date)]
            else:
                df = df.loc[df.index >= start_date]
        if end_date is not None:
            df = df.loc[df.index <= end_date]
        if title is None or title == "":
            if all(x == trimmed_tables[0] for x in trimmed_tables):
                title_text = trimmed_tables[0]
            else:
                title_text = "<br>".join(trimmed_tables)
        else:
            title_text = title
        if subtitle is not None and subtitle != "":
            title_text = f"{title_text}<br><span style='font-size: 14px'>{subtitle}</span>"
        height = 600 + 20 * len(set(trimmed_tables))
        df_chart = df.reset_index()
        df_chart.columns = df_chart.columns.get_level_values(0)
        export_name = uuid.uuid4().hex
        if chart_type != "table":
            if chart_type == "bar":
                fig = px.bar(df_chart, x="index", y=df_chart.columns,
                             height=height, title=title_text,
                             color_discrete_sequence=px.colors.qualitative.Vivid,
                             barmode="group", template="plotly_white")
            elif chart_type == "stackbar":
                fig = px.bar(df_chart, x="index", y=df_chart.columns,
                             height=height, title=title_text,
                             color_discrete_sequence=px.colors.qualitative.Vivid,
                             barmode="stack", template="plotly_white")
            elif chart_type == "area":
                fig = px.area(df_chart, x="index", y=df_chart.columns,
                              height=height, title=title_text,
                              color_discrete_sequence=px.colors.qualitative.Vivid,
                              template="plotly_white")
            elif chart_type == "normarea":
                fig = px.area(df_chart, x="index", y=df_chart.columns,
                              height=height, title=title_text,
                              color_discrete_sequence=px.colors.qualitative.Vivid,
                              template="plotly_white", groupnorm="fraction")
            else:
                fig = px.line(df_chart, x="index", y=df_chart.columns,
                              height=height, title=title_text,
                              color_discrete_sequence=px.colors.qualitative.Vivid,
                              template="plotly_white")
            for label, trace in zip(labels, fig.select_traces()):
                trace.update(name=label)
            ylabels = []
            for currency, unit, inf in zip(
                    list(df.columns.get_level_values("Moneda")),
                    list(df.columns.get_level_values("Unidad")),
                    list(df.columns.get_level_values("Inf. adj."))):
                text = []
                if currency != "-":
                    text += [currency]
                text += [unit]
                if inf != "No":
                    text += [inf]
                ylabels.append(" | ".join(text))
            if all(x == ylabels[0] for x in ylabels):
                ylabels = ylabels[0]
            else:
                ylabels = ""
            fig.update_layout({"margin": {"l": 0, "r": 15},
                               "legend": {"orientation": "h", "yanchor": "top",
                                          "y": -0.1, "xanchor": "left",
                                          "x": 0},
                               "legend_orientation": "h",
                               "xaxis_title": "",
                               "yaxis_title": ylabels,
                               "legend_title": "",
                               "title": {"y": 0.9,
                                         "yanchor": "top",
                                         "font": {"size": 20}}})
            path_to_logo = path.join(current_app.root_path,
                                     "static", "cards.jpg")
            fig.add_layout_image(dict(source=Image.open(path_to_logo),
                                      sizex=0.1, sizey=0.1, xanchor="right",
                                      yanchor="bottom", xref="paper",
                                      yref="paper",
                                      x=1, y=1.01))
            fig.update_xaxes(
                rangeselector=dict(yanchor="bottom", y=1.01, xanchor="right",
                                   x=0.9,
                                   buttons=list([
                                       dict(count=1, label="1m", step="month",
                                            stepmode="backward"),
                                       dict(count=6, label="6m", step="month",
                                            stepmode="backward"),
                                       dict(count=1, label="YTD", step="year",
                                            stepmode="todate"),
                                       dict(count=1, label="1a", step="year",
                                            stepmode="backward"),
                                       dict(count=5, label="5a", step="year",
                                            stepmode="backward"),
                                       dict(label="todos", step="all")
                                   ])
                                   )
            )
            viz = dcc.Graph(figure=fig)
            export_folder = path.join(current_app.root_path,
                                      current_app.config["EXPORT_FOLDER"])
            if not path.exists(export_folder):
                mkdir(export_folder)
            html_name = f"{export_name}.html"
            fig.write_html(path.join(export_folder, html_name),
                           include_plotlyjs="cdn", full_html=False)
            html_href = f"/viz/dl_html?html_name={html_name}"
            html_style = {"display": "inline-block", "margin": "10px"}
        else:
            html_href = ""
            html_style = {"display": "none"}
            table_df = df.copy()
            table_df.columns = table_df.columns.get_level_values(0)
            table_df.reset_index(inplace=True)
            table_df.rename(columns={"index": "Fecha"}, inplace=True)
            table_df["Fecha"] = table_df["Fecha"].dt.strftime("%d-%m-%Y")
            viz = html.Div([html.Br(),
                            dt.DataTable(id="table",
                                         columns=[{"name": "Fecha",
                                                   "id": "Fecha",
                                                   "type": "datetime"}] +
                                                 [{"name": i, "id": i,
                                                   "type": "numeric",
                                                   "format":
                                                       Format(precision=2,
                                                              scheme=Scheme.fixed,
                                                              group=Group.yes,
                                                              groups=3,
                                                              group_delimiter=",",
                                                              decimal_delimiter=".")}
                                                  for i in
                                                  table_df.columns[1:]],
                                         data=table_df.to_dict("records"),
                                         style_cell={"textAlign": "center"},
                                         style_header={
                                             "whiteSpace": "normal",
                                             "height": "auto",
                                             "textAlign": "center"},
                                         page_action="none",
                                         fixed_rows={"headers": True})])
        notes_tables = [table for table, indicator in zip(table_s, indicator_s)
                        if table is not None and indicator != []]
        notes = build_metadata(tables=notes_tables, dfs=dataframes,
                               transformations=arr_orders_s)
        export_name = f"export_{uuid.uuid4().hex}"
        href = f"/viz/dl?name={export_name}"
        if len(set(valid_tables)) > 1:
            metadata = df.columns.to_frame(index=False)
            metadata.to_sql(name=f"{export_name}_metadata",
                            con=db.get_engine(bind="queries"))
            columns = df.columns.get_level_values(0)
            new_columns = ["_".join(x.split("_")[1:]) for x in columns]
            df.columns = new_columns
            df.to_sql(name=f"{export_name}",
                      con=db.get_engine(bind="queries"))
        else:
            sqlutil.df_to_sql(df, name=export_name,
                              con=db.get_engine(bind="queries"))
        return (viz,
                {"display": "block"}, notes, href, {"display": "inline-block",
                                                    "margin": "10px"},
                html_href, html_style,
                True, "success", html.P("Visualización actualizada👇",
                                        className="mb-0"))

    @app.callback(
        Output("indicator-container", "children"),
        [Input("add-indicator", "n_clicks")],
        [State("indicator-container", "children")])
    def display_dropdowns(n_clicks, children):
        short_br = html.Div(style={"height": "5px"})

        options = [{"label": v, "value": k} if "-----" not in v
                   else {"label": v, "value": k, "disabled": True}
                   for k, v in table_options.items()]
        table_dropdown = dcc.Dropdown(id={
            "type": "table-dropdown",
            "index": n_clicks
        },
            options=options,
            placeholder="Seleccionar cuadro", optionHeight=50
        )

        indicator_dropdown = dcc.Loading(
            id="indicator-loading",
            children=[dcc.Dropdown(id={"type": "indicator-dropdown",
                                       "index": n_clicks},
                                   placeholder="Seleccionar indicador",
                                   optionHeight=50, multi=True,
                                   disabled=True)],
            type="default")

        usd = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "usd-check",
                    "index": n_clicks},
                    options=[
                        {"label": "Convertir a dólares",
                         "value": True}], value=[],
                    inputStyle={"margin-right": "10px"})]),
            order_dropdown(number="1", n_clicks=n_clicks),
            details("Las selecciones de *orden* definen qué "
                    "transformación se aplica en qué orden, siendo "
                    "*orden=1* la primera")])

        real = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "real-check",
                    "index": n_clicks
                }, options=[{"label": "Deflactar",
                             "value": True}], value=[],
                    inputStyle={"margin-right": "10px"})]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.DatePickerRange(id={
                         "type": "real-range",
                         "index": n_clicks},
                         start_date_placeholder_text="Fecha inicial",
                         end_date_placeholder_text="Fecha final",
                         display_format="DD-MM-YYYY", disabled=True)]),
            order_dropdown(number="2", n_clicks=n_clicks),
            details(
                "Es posible deflactar a) definiendo solo la fecha de inicio "
                "para que los datos queden expresados a precios de ese mes, b)"
                " definiendo ambas para que los datos queden expresados a "
                "precios promedio de ese rango de meses, c) sin definir "
                "fechas.")])

        gdp = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "gdp-check",
                    "index": n_clicks},
                    options=[
                        {"label": "Convertir a % del PBI",
                         "value": True}], value=[],
                    inputStyle={"margin-right": "10px"})]),
            order_dropdown(number="3", n_clicks=n_clicks)])

        res = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "resample-check",
                    "index": n_clicks
                }, options=[{"label": "Cambiar frecuencia",
                             "value": True}], value=[],
                    inputStyle={"margin-right": "10px"})]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "resample-frequency",
                         "index": n_clicks
                     }, options=[{"label": "Anual", "value": "A-DEC"},
                                 {"label": "Trimestral", "value": "Q-DEC"},
                                 {"label": "Mensual", "value": "M"},
                                 {"label": "14 días", "value": "2W"},
                                 {"label": "Semanal", "value": "W"}],
                         placeholder="Frecuencia", style={"width": "150px"},
                         searchable=False, disabled=True)]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "resample-operation",
                         "index": n_clicks
                     }, options=[
                         {"label": "Reducir frecuencia: promedio",
                          "value": "average"},
                         {"label": "Reducir frecuencia: suma",
                          "value": "sum"},
                         {"label": "Reducir frecuencia: último período",
                          "value": "end"},
                         {"label": "Aumentar frecuencia",
                          "value": "upsample"}],
                         placeholder="Método", style={"width": "300px"},
                         searchable=False, disabled=True)]),
            order_dropdown(number="4", n_clicks=n_clicks)])

        roll = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "rolling-check",
                    "index": n_clicks
                }, options=[{"label": "Acumular",
                             "value": True}], value=[],
                    inputStyle={"margin-right": "10px"})]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dbc.Input(id={
                         "type": "rolling-periods",
                         "index": n_clicks
                     }, type="number", placeholder="Períodos",
                         style={"width": "100px"}, disabled=True,
                         debounce=True)]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "rolling-operation",
                         "index": n_clicks
                     }, options=[{"label": "Suma", "value": "sum"},
                                 {"label": "Promedio", "value": "average"}],
                         placeholder="Operación", style={"width": "120px"},
                         searchable=False, disabled=True)]),
            order_dropdown(number="5", n_clicks=n_clicks)])

        base_index = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "base-check",
                    "index": n_clicks
                }, options=[{"label": "Calcular índice base",
                             "value": True}], value=[],
                    inputStyle={"margin-right": "10px"})]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.DatePickerRange(id={
                         "type": "base-range",
                         "index": n_clicks},
                         start_date_placeholder_text="Fecha inicial",
                         end_date_placeholder_text="Fecha final",
                         display_format="DD-MM-YYYY", disabled=True)]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dbc.Input(id={
                         "type": "base-base",
                         "index": n_clicks
                     }, type="number", placeholder="Valor base",
                         style={"width": "150px"}, disabled=True,
                         debounce=True)]),
            order_dropdown(number="6", n_clicks=n_clicks),
            details(
                "La fecha final es opcional, en cuyo caso el índice será "
                "*valor de fecha inicial=valor base*. Si se define fecha "
                "final, el índice será *promedio de valores entre fecha "
                "inicial y fecha final=valor base*.")])

        chg_diff = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "chg-diff-check",
                    "index": n_clicks
                }, options=[{"label": "Calcular variaciones o diferencias",
                             "value": True}], value=[],
                    inputStyle={"margin-right": "10px"})]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "chg-diff-operation",
                         "index": n_clicks
                     }, options=[
                         {"label": "Variación porcentual", "value": "chg"},
                         {"label": "Diferencia", "value": "diff"}],
                         placeholder="Tipo", style={"width": "200px"},
                         searchable=False, disabled=True)]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "chg-diff-period",
                         "index": n_clicks
                     }, options=[{"label": "Último período", "value": "last"},
                                 {"label": "Interanual", "value": "inter"},
                                 {"label": "Anual", "value": "annual"}],
                         placeholder="Operación", style={"width": "150px"},
                         searchable=False, disabled=True)]),
            order_dropdown(number="7", n_clicks=n_clicks)])

        seas = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "seas-check",
                    "index": n_clicks
                }, options=[{"label": "Desestacionalizar",
                             "value": True}], value=[],
                    inputStyle={"margin-right": "10px"})]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "seas-method",
                         "index": n_clicks
                     }, options=[{"label": "Loess", "value": "loess"},
                                 {"label": "Medias móviles", "value": "ma"},
                                 {"label": "X13 ARIMA", "value": "x13"}],
                         placeholder="Método", style={"width": "200px"},
                         searchable=False, disabled=True)]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "seas-type",
                         "index": n_clicks
                     }, options=[
                         {"label": "Desestacionalizado", "value": "seas"},
                         {"label": "Tendencia-ciclo", "value": "trend"}],
                         placeholder="Componente", style={"width": "200px"},
                         searchable=False, disabled=True)]),
            order_dropdown(number="8", n_clicks=n_clicks),
            details("El procesamiento con el método X13 ARIMA puede demorar "
                    "dependiendo del tipo y largo de series en la tabla "
                    "seleccionada. En algunos casos la consulta puede ser "
                    "terminada.")])

        complete_div = html.Div(children=[table_dropdown, short_br,
                                          indicator_dropdown, html.Br(), usd,
                                          short_br, real, short_br, gdp,
                                          short_br, res, short_br, roll,
                                          short_br, base_index, short_br,
                                          chg_diff, short_br, seas, html.Br()],
                                id={"type": "complete-div", "index": n_clicks})
        hide_button = dbc.Button("Colapsar conjunto de indicadores", id={
            "type": "hide-button",
            "index": n_clicks}, style={"display": "block"}, color="dark")
        children.extend([hide_button, complete_div])
        return children

    @app.callback(
        [Output({"type": "order-1", "index": MATCH}, "disabled"),
         Output({"type": "real-range", "index": MATCH}, "disabled"),
         Output({"type": "order-2", "index": MATCH}, "disabled"),
         Output({"type": "order-3", "index": MATCH}, "disabled"),
         Output({"type": "resample-frequency", "index": MATCH}, "disabled"),
         Output({"type": "resample-operation", "index": MATCH}, "disabled"),
         Output({"type": "order-4", "index": MATCH}, "disabled"),
         Output({"type": "rolling-periods", "index": MATCH}, "disabled"),
         Output({"type": "rolling-operation", "index": MATCH}, "disabled"),
         Output({"type": "order-5", "index": MATCH}, "disabled"),
         Output({"type": "base-range", "index": MATCH}, "disabled"),
         Output({"type": "base-base", "index": MATCH}, "disabled"),
         Output({"type": "order-6", "index": MATCH}, "disabled"),
         Output({"type": "chg-diff-operation", "index": MATCH}, "disabled"),
         Output({"type": "chg-diff-period", "index": MATCH}, "disabled"),
         Output({"type": "order-7", "index": MATCH}, "disabled"),
         Output({"type": "seas-method", "index": MATCH}, "disabled"),
         Output({"type": "seas-type", "index": MATCH}, "disabled"),
         Output({"type": "order-8", "index": MATCH}, "disabled")],
        [Input({"type": "usd-check", "index": MATCH}, "value"),
         Input({"type": "real-check", "index": MATCH}, "value"),
         Input({"type": "gdp-check", "index": MATCH}, "value"),
         Input({"type": "resample-check", "index": MATCH}, "value"),
         Input({"type": "rolling-check", "index": MATCH}, "value"),
         Input({"type": "base-check", "index": MATCH}, "value"),
         Input({"type": "chg-diff-check", "index": MATCH}, "value"),
         Input({"type": "seas-check", "index": MATCH}, "value")])
    def enable_options(usd, real, gdp, resample, rolling,
                       base, chg_diff, seas):
        outputs = [True] * 19
        if True in usd:
            outputs[0] = False
        if True in real:
            outputs[1], outputs[2] = False, False
        if True in gdp:
            outputs[3] = False
        if True in resample:
            outputs[4], outputs[5], outputs[6] = False, False, False
        if True in rolling:
            outputs[7], outputs[8], outputs[9] = False, False, False
        if True in base:
            outputs[10], outputs[11], outputs[12] = False, False, False
        if True in chg_diff:
            outputs[13], outputs[14], outputs[15] = False, False, False
        if True in seas:
            outputs[16], outputs[17], outputs[18] = False, False, False
        return outputs

    @app.callback(
        [Output({"type": "indicator-dropdown", "index": MATCH}, "options"),
         Output({"type": "indicator-dropdown", "index": MATCH}, "disabled")],
        [Input({"type": "table-dropdown", "index": MATCH}, "value")])
    def indicator_dropdowns(table):
        if not table:
            raise PreventUpdate
        df = sqlutil.read(con=db.engine, table_name=table)
        columns = df.columns.get_level_values(0)
        return ([{"label": "Todos los indicadores", "value": "*"}]
                + [{"label": v, "value": v} for v in columns]), False

    @app.callback(
        [Output({"type": "complete-div", "index": MATCH}, "style"),
         Output({"type": "hide-button", "index": MATCH}, "children")],
        [Input({"type": "hide-button", "index": MATCH}, "n_clicks")])
    def toggle_hide_indicators(n_clicks):
        if n_clicks is None:
            return {"display": "block"}, "Colapsar conjunto de indicadores"
        elif n_clicks % 2 != 0:
            return {"display": "none"}, "Mostrar conjunto de indicadores"
        else:
            return {"display": "block"}, "Colapsar conjunto de indicadores"

    @app.callback(
        [Output("metadata", "style"),
         Output("metadata-button", "children")],
        [Input("metadata-button", "n_clicks")])
    def toggle_hide_metadata(n_clicks):
        if n_clicks is None:
            return {"display": "none"}, "Desplegar metadatos"
        elif n_clicks % 2 != 0:
            return {"display": "block"}, "Colapsar metadatos"
        else:
            return {"display": "none"}, "Desplegar metadatos"

    @app.server.route("/viz/dl")
    def export_data():
        name = request.args.get("name")
        try:
            data = sqlutil.read(con=db.get_engine(bind="queries"),
                                table_name=name)
            credit = pd.DataFrame(columns=data.columns, index=[np.nan] * 2)
            credit.iloc[1, 0] = "https://econ.uy"
            output = data.append(credit)
        except ProgrammingError:
            return flash("La tabla ya no está disponible para descargar. "
                         "Intente la consulta nuevamente.")
        db.engine.execute(f'DROP TABLE IF EXISTS "{name}"')
        db.engine.execute(f'DROP TABLE IF EXISTS "{name}_metadata"')
        bio = BytesIO()
        writer = pd.ExcelWriter(bio, engine="xlsxwriter")
        output.to_excel(writer, sheet_name="Sheet1")
        writer.save()
        bio.seek(0)
        return send_file(bio, mimetype='application/vnd.openxmlformats-'
                                       'officedocument.spreadsheetml.sheet',
                         attachment_filename="econuy-data.xlsx",
                         as_attachment=True, cache_timeout=0)

    @app.server.route("/viz/dl_html")
    def export_html():
        name = request.args.get("html_name")
        directory = path.join(current_app.root_path,
                              current_app.config["EXPORT_FOLDER"])
        return send_from_directory(filename=name, directory=directory,
                                   attachment_filename="econuy-plot.html",
                                   as_attachment=True, cache_timeout=0,
                                   mimetype="text/html")


def order_dropdown(number: str, n_clicks):
    return html.Div(
        style={"display": "inline-block", "margin-left": "10px",
               "vertical-align": "middle"},
        children=[
            html.Div(children=dcc.Dropdown(
                id={"type": f"order-{number}",
                    "index": n_clicks},
                options=[{"label": i, "value": i} for i in range(1, 9)],
                placeholder="Orden", clearable=False,
                style={"width": "100px"},
                searchable=False, disabled=True),
                style={"display": "inline-block",
                       "vertical-align": "middle"})])


def details(text: str):
    return html.Div(html.Details([
        html.Summary(html.Img(src=url_for("static", filename="info.png"),
                              width=22)),
        dcc.Markdown(f'''{text}''', style={"color": "gray",
                                           "font-size": "13px"})]),
        style={"display": "inline-block", "margin-left": "10px",
               "vertical-align": "middle"})


def define_order(submit_order, all_transforms):
    pruned_order = {k: v for k, v in submit_order.items()
                    if all_transforms[k] is True}
    aux = sorted(pruned_order, key=pruned_order.get)
    return dict(zip(list(range(len(aux))), aux))


def fix_freqs_and_names(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    freqs = []
    dfs = unique_names(dfs=dfs)
    for df in dfs:
        freqs.append(pd.infer_freq(df.index))
    if all(freq == freqs[0] for freq in freqs):
        return pd.concat(dfs, axis=1)
    else:
        for freq_opt in ["A-DEC", "A", "Q-DEC", "Q", "M", "2W-SUN", "W-SUN"]:
            if freq_opt in freqs:
                output = []
                for df in dfs:
                    freq_df = pd.infer_freq(df.index)
                    if freq_df == freq_opt:
                        df_match = df.copy()
                    else:
                        type_df = df.columns.get_level_values("Tipo")[0]
                        unit_df = df.columns.get_level_values("Unidad")[0]
                        if type_df == "Stock":
                            df_match = transform.resample(df, target=freq_opt,
                                                          operation="end")
                        elif (type_df == "Flujo" and
                              not any(x in unit_df for
                                      x in ["%", "=", "Cambio"])):
                            df_match = transform.resample(df, target=freq_opt,
                                                          operation="sum")
                        else:
                            df_match = transform.resample(df, target=freq_opt,
                                                          operation="average")
                    output.append(df_match)
                return pd.concat(output, axis=1)
        if None in freqs:
            return pd.concat(dfs, axis=1)


def unique_names(dfs: List[pd.DataFrame]) -> List[pd.DataFrame]:
    names = []
    new_dfs = []
    i = 0
    for df in dfs:
        df_names = []
        new_names = df.columns.levels[0]
        for name in new_names:
            if name in names:
                i += 1
                names.append(f"{name}_{i}")
                df_names.append(f"{name}_{i}")
            else:
                names.append(name)
                df_names.append(name)
        df.columns.set_levels(df_names, level=0, inplace=True)
        new_dfs.append(df)
    return new_dfs


def build_metadata(tables: List[str], dfs: List[pd.DataFrame],
                   transformations: List[Dict]):
    transformation_labels = {"usd": "Convertir a dólares",
                             "real": "Deflactar",
                             "gdp": "Convertir a % del PBI",
                             "res": "Cambiar frecuencia",
                             "roll": "Acumular",
                             "base_index": "Calcular índice base",
                             "chg_diff": "Calcular variaciones o diferencias",
                             "seas": "Desestacionalizar"}
    divs = []
    for table, df, transformation in zip(tables, dfs, transformations):
        table_text = html.H4(table_options[table])
        meta = []
        for i in range(9):
            meta.append(list(df.columns.get_level_values(i)))
        metadata_text = []
        for counter, indicator in enumerate(meta[0]):
            valid_tables = [x for x in tables if x is not None]
            if len(set(valid_tables)) > 1:
                indicator = indicator.split("_")[1]
            metadata_text.append(
                html.Div([html.H5(indicator),
                          f"Frecuencia: {meta[2][counter]}", html.Br(),
                          f"Moneda: {meta[3][counter]}", html.Br(),
                          f"Ajuste precios: {meta[4][counter]}", html.Br(),
                          f"Unidad: {meta[5][counter]}", html.Br(),
                          f"Descomposición: {meta[6][counter]}", html.Br(),
                          f"Tipo: {meta[7][counter]}", html.Br(),
                          f"Períodos acumulados: {meta[8][counter]}",
                          html.Br(), html.Br()]))
        transformation_text = []
        for t in transformation.values():
            transformation_text.append(transformation_labels[t])
        if len(transformation_text) == 0:
            transformation_text = [html.Div("Ninguna transformación aplicada"),
                                   html.Br()]
        else:
            items = []
            for text in transformation_text:
                items.append(html.Li(text))
            transformation_text = [html.Ul(items)]
        sources = metadata._get_sources(dataset=table, html_urls=False)
        if len(sources[0]) > 0:
            direct = [dcc.Link(number + 1, href=url, target="_parent")
                      for number, url in enumerate(sources[0])]
            separated_direct = []
            for link in direct:
                separated_direct.append(" | ")
                separated_direct.append(link)
            separated_direct = separated_direct[1:]
        else:
            separated_direct = ["no disponible"]
        indirect = [dcc.Link(number + 1, href=url, target="_parent")
                    for number, url in enumerate(sources[1])]
        separated_indirect = []
        for link in indirect:
            separated_indirect.append(" | ")
            separated_indirect.append(link)
        separated_indirect = separated_indirect[1:]
        sources_text = [html.H5("Fuentes"),
                        html.Ul(
                            [html.Li(["Links directos: "] + separated_direct),
                             html.Li(
                                 ["Links indirectos: "] + separated_indirect),
                             html.Li(
                                 "Proveedores: " + " | ".join(sources[2]))])]
        divs.extend([table_text] + [html.Br()] +
                    metadata_text + [html.H5("Transformaciones")]
                    + transformation_text + sources_text + [html.Hr()])
    return divs[:-1]
