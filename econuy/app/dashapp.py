import re
from typing import List

import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
from dash import Dash
from dash.dependencies import Input, Output, State, ALL, MATCH
from flask import url_for

from econuy import transform
from econuy.app.app_strings import table_options
from econuy.utils import sqlutil

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

url_base = "/dash/viz/"


def add_dash(server, options):
    app = Dash(server=server, url_base_pathname=url_base,
               external_stylesheets=external_stylesheets)
    app.layout = html.Div([html.H1("Visualizador econuy"),
                           html.Button("Agregar indicador", id="add-indicator",
                                       n_clicks=0),
                           html.Br(), html.Br(),
                           html.Div(id="indicator-container",
                                    children=[]),
                           html.Br(),
                           html.Div(
                               id="chart-type-container",
                               style={"display": "none"},
                               children=[
                                   "Tipo de gráfico",
                                   dcc.RadioItems(
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
                                                 "value": "normarea"}],
                                       value="line",
                                       labelStyle={"display": "inline-block"},
                                       style={"display": "inline-block"})]),
                           html.Div(style={"height": "5px"}),
                           html.Div(id="date-range-container",
                                    style={"display": "none"},
                                    children=["Filtrar fechas",
                                              dcc.DatePickerRange(
                                                  id="date-picker",
                                                  start_date_placeholder_text="Fecha inicial",
                                                  end_date_placeholder_text="Fecha final",
                                                  display_format="DD-MM-YYYY")]),
                           dcc.Graph(id="chart", style={"display": "none"})])

    register_callbacks(app, options=options)

    return app.server


def register_callbacks(app, options):
    from econuy.app import db

    @app.callback(
        [Output("chart", "figure"),
         Output("chart", "style"),
         Output("chart-type-container", "style"),
         Output("date-range-container", "style")],
        [Input("chart-type", "value"),
         Input({"type": "indicator-dropdown", "index": ALL}, "value"),
         Input({"type": "usd-check", "index": ALL}, "value"),
         Input({"type": "real-check", "index": ALL}, "value"),
         Input({"type": "real-range", "index": ALL}, "start_date"),
         Input({"type": "real-range", "index": ALL}, "end_date"),
         Input({"type": "gdp-check", "index": ALL}, "value"),
         Input({"type": "resample-check", "index": ALL}, "value"),
         Input({"type": "resample-frequency", "index": ALL}, "value"),
         Input({"type": "resample-operation", "index": ALL}, "value"),
         Input({"type": "rolling-check", "index": ALL}, "value"),
         Input({"type": "rolling-periods", "index": ALL}, "value"),
         Input({"type": "rolling-operation", "index": ALL}, "value"),
         Input({"type": "base-check", "index": ALL}, "value"),
         Input({"type": "base-range", "index": ALL}, "start_date"),
         Input({"type": "base-range", "index": ALL}, "end_date"),
         Input({"type": "base-base", "index": ALL}, "value"),
         Input({"type": "chg-diff-check", "index": ALL}, "value"),
         Input({"type": "chg-diff-operation", "index": ALL}, "value"),
         Input({"type": "chg-diff-period", "index": ALL}, "value"),
         Input({"type": "seas-check", "index": ALL}, "value"),
         Input({"type": "seas-method", "index": ALL}, "value"),
         Input({"type": "seas-type", "index": ALL}, "value"),
         Input({"type": "order-1", "index": ALL}, "value"),
         Input({"type": "order-2", "index": ALL}, "value"),
         Input({"type": "order-3", "index": ALL}, "value"),
         Input({"type": "order-4", "index": ALL}, "value"),
         Input({"type": "order-5", "index": ALL}, "value"),
         Input({"type": "order-6", "index": ALL}, "value"),
         Input({"type": "order-7", "index": ALL}, "value"),
         Input({"type": "order-8", "index": ALL}, "value"),
         Input("date-picker", "start_date"),
         Input("date-picker", "end_date")])
    def update_df(chart_type, indicator_s, usd_s, real_s, real_start_s,
                  real_end_s, gdp_s, resample_s, resample_frequency_s,
                  resample_operation_s, rolling_s, rolling_period_s,
                  rolling_operation_s, base_index_s, base_start_s,
                  base_end_s, base_base_s, chg_diff_s, chg_diff_operation_s,
                  chg_diff_period_s, seas_s, seas_method_s,
                  seas_type_s, orders_1_s, order_2_s, order_3_s,
                  order_4_s, order_5_s, order_6_s, order_7_s, order_8_s,
                  start_date, end_date):
        dataframes = []
        labels = []
        for (indicator,
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
             order_8) in zip(indicator_s,
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
            if indicator is None:
                continue
            try:
                split = indicator.split(">")
                table = split[0]
                column = split[1]
                trimmed_table = re.sub(r" \(([^)]+)\)$", "",
                                       table_options[table])
                labels.append(f"{trimmed_table}_{column}")
            except AttributeError:
                pass
            df_aux = sqlutil.read(con=db.engine, table_name=table, cols=column)
            column_names = [f"{table_options[table]} | {column}"]
            df_aux.columns.set_levels(
                column_names,
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
            function_dict = {
                "usd": lambda x: transform.convert_usd(x, update_loc=db.engine,
                                                       only_get=True),
                "real": lambda x: transform.convert_real(
                    x, update_loc=db.engine, only_get=True,
                    start_date=real_start,
                    end_date=real_end),
                "gdp": lambda x: transform.convert_gdp(x, update_loc=db.engine,
                                                       only_get=True),
                "res": lambda x: transform.resample(x,
                                                    target=resample_frequency,
                                                    operation=resample_operation),
                "roll": lambda x: transform.rolling(x,
                                                    periods=rolling_periods,
                                                    operation=rolling_operations),
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

        if len(dataframes) == 0:
            return [], {"display": "none"}, {"display": "none"}, {
                "display": "none"}
        df = match_freqs(dataframes)
        df = df.dropna(how="all", axis=0)
        if start_date is not None:
            if end_date is not None:
                df = df.loc[(df.index >= start_date) & (df.index <= end_date)]
            else:
                df = df.loc[df.index >= start_date]
        if end_date is not None:
            df = df.loc[df.index <= end_date]

        if chart_type == "bar":
            fig = px.bar(df, x=df.index, height=600,
                         y=list(df.columns.get_level_values(level=0)),
                         title="econuy.VIZ",
                         color_discrete_sequence=px.colors.qualitative.Vivid,
                         barmode="group", template="plotly_white")
        elif chart_type == "stackbar":
            fig = px.bar(df, x=df.index, height=600,
                         y=list(df.columns.get_level_values(level=0)),
                         title="econuy.VIZ",
                         color_discrete_sequence=px.colors.qualitative.Vivid,
                         barmode="stack", template="plotly_white")
        elif chart_type == "area":
            fig = px.area(df, x=df.index, height=600,
                          y=list(df.columns.get_level_values(level=0)),
                          title="econuy.VIZ",
                          color_discrete_sequence=px.colors.qualitative.Vivid,
                          template="plotly_white")
        elif chart_type == "normarea":
            fig = px.area(df, x=df.index, height=600,
                          y=list(df.columns.get_level_values(level=0)),
                          title="econuy.VIZ",
                          color_discrete_sequence=px.colors.qualitative.Vivid,
                          template="plotly_white", groupnorm="fraction")
        else:
            fig = px.line(df, x=df.index, height=600,
                          y=list(df.columns.get_level_values(level=0)),
                          title="econuy.VIZ",
                          color_discrete_sequence=px.colors.qualitative.Vivid,
                          template="plotly_white")
        for label, trace in zip(labels, fig.select_traces()):
            trace.update(name=label)
        fig.update_layout({"margin": {"l": 0, "r": 15},
                           "legend": {"orientation": "h", "yanchor": "top",
                                      "y": -0.1, "xanchor": "left", "x": 0},
                           "legend_orientation": "h",
                           "xaxis_title": "",
                           "yaxis_title": "",
                           "legend_title": "",
                           "title": {"y": 0.9,
                                     "yanchor": "top",
                                     "font": {"size": 30}}})
        fig.add_layout_image(dict(source=url_for("static",
                                                 filename="logo.png"),
                                  sizex=0.1, sizey=0.1, xanchor="right",
                                  yanchor="bottom", xref="paper", yref="paper",
                                  x=1, y=1.01))
        return fig, {"display": "block"}, {"display": "block"}, {
            "display": "block"}

    @app.callback(
        Output("indicator-container", "children"),
        [Input("add-indicator", "n_clicks")],
        [State("indicator-container", "children")])
    def display_dropdowns(n_clicks, children, opts=options):
        short_br = html.Div(style={"height": "5px"})

        indicator_dropdown = dcc.Dropdown(
            id={
                "type": "indicator-dropdown",
                "index": n_clicks
            },
            options=opts, placeholder="Seleccionar indicador",
            optionHeight=50
        )

        usd = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "usd-check",
                    "index": n_clicks},
                    options=[
                        {"label": "Convertir a dólares",
                         "value": True}], value=[])]),
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
                             "value": True}], value=[])]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.DatePickerRange(id={
                         "type": "real-range",
                         "index": n_clicks},
                         start_date_placeholder_text="Fecha inicial",
                         end_date_placeholder_text="Fecha final",
                         display_format="DD-MM-YYYY")]),
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
                         "value": True}], value=[])]),
            order_dropdown(number="3", n_clicks=n_clicks)])

        res = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "resample-check",
                    "index": n_clicks
                }, options=[{"label": "Cambiar frecuencia",
                             "value": True}], value=[])]),
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
                         placeholder="Frecuencia", style={"width": "150px"})]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "resample-operation",
                         "index": n_clicks
                     }, options=[{"label": "Reducir frecuencia: promedio",
                                  "value": "average"},
                                 {"label": "Reducir frecuencia: suma",
                                  "value": "sum"},
                                 {
                                     "label": "Reducir frecuencia: último período",
                                     "value": "end"},
                                 {"label": "Aumentar frecuencia",
                                  "value": "upsample"}],
                         placeholder="Método", style={"width": "250px"})]),
            order_dropdown(number="4", n_clicks=n_clicks)])

        roll = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "rolling-check",
                    "index": n_clicks
                }, options=[{"label": "Acumular",
                             "value": True}], value=[])]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Input(id={
                         "type": "rolling-periods",
                         "index": n_clicks
                     }, type="number", placeholder="Períodos",
                         style={"width": "100px"})]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "rolling-operation",
                         "index": n_clicks
                     }, options=[{"label": "Suma", "value": "sum"},
                                 {"label": "Promedio", "value": "average"}],
                         placeholder="Operación", style={"width": "120px"})]),
            order_dropdown(number="5", n_clicks=n_clicks)])

        base_index = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "base-check",
                    "index": n_clicks
                }, options=[{"label": "Calcular índice base",
                             "value": True}], value=[])]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.DatePickerRange(id={
                         "type": "base-range",
                         "index": n_clicks},
                         start_date_placeholder_text="Fecha inicial",
                         end_date_placeholder_text="Fecha final",
                         display_format="DD-MM-YYYY")]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Input(id={
                         "type": "base-base",
                         "index": n_clicks
                     }, type="number", placeholder="Valor base",
                         style={"width": "150px"})]),
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
                             "value": True}], value=[])]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "chg-diff-operation",
                         "index": n_clicks
                     }, options=[
                         {"label": "Variación porcentual", "value": "chg"},
                         {"label": "Cambio", "value": "diff"}],
                         placeholder="Tipo", style={"width": "200px"})]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "chg-diff-period",
                         "index": n_clicks
                     }, options=[{"label": "Último período", "value": "last"},
                                 {"label": "Interanual", "value": "inter"},
                                 {"label": "Anual", "value": "annual"}],
                         placeholder="Operación", style={"width": "150px"})]),
            order_dropdown(number="7", n_clicks=n_clicks)])

        seas = html.Div(children=[
            html.Div(
                style={"vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    "type": "seas-check",
                    "index": n_clicks
                }, options=[{"label": "Desestacionalizar",
                             "value": True}], value=[])]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "seas-method",
                         "index": n_clicks
                     }, options=[{"label": "Loess", "value": "loess"},
                                 {"label": "Medias móviles", "value": "ma"},
                                 {"label": "X13 ARIMA", "value": "x13"}],
                         placeholder="Método", style={"width": "200px"})]),
            html.Div(style={"display": "inline-block", "margin-left": "10px",
                            "vertical-align": "middle"},
                     children=[dcc.Dropdown(id={
                         "type": "seas-type",
                         "index": n_clicks
                     }, options=[
                         {"label": "Desestacionalizado", "value": "seas"},
                         {"label": "Tendencia-ciclo", "value": "trend"}],
                         placeholder="Componente", style={"width": "150px"})]),
            order_dropdown(number="8", n_clicks=n_clicks),
            details("El procesamiento con el método X13 ARIMA puede demorar "
                    "dependiendo del tipo y largo de series en la tabla "
                    "seleccionada. En algunos casos la consulta puede ser "
                    "terminada.")])

        complete_div = html.Div(children=[indicator_dropdown, html.Br(), usd,
                                          short_br, real, short_br, gdp,
                                          short_br, res, short_br, roll,
                                          short_br, base_index, short_br,
                                          chg_diff, short_br, seas], id={
            "type": "complete-div",
            "index": n_clicks})
        hide_button = html.Button("Colapsar", id={
            "type": "hide-button",
            "index": n_clicks}, style={"display": "block"})
        children.extend([hide_button, complete_div])
        return children

    @app.callback(
        [Output({"type": "complete-div", "index": MATCH}, "style"),
         Output({"type": "hide-button", "index": MATCH}, "children")],
        [Input({"type": "hide-button", "index": MATCH}, "n_clicks")])
    def toggle_hide(n_clicks):
        if n_clicks is None:
            return {"display": "block"}, "Colapsar indicador"
        elif n_clicks % 2 != 0:
            return {"display": "none"}, "Mostrar indicador"
        else:
            return {"display": "block"}, "Colapsar indicador"


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
                style={"width": "100px"}),
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


def match_freqs(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    dfs = unique_names(dfs=dfs)
    freqs = []
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
                        if type_df == "Stock":
                            df_match = transform.resample(df, target=freq_opt,
                                                          operation="end")
                        elif type_df == "Flujo":
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
        new_names = list(df.columns.get_level_values(0))
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
