from os import path
from io import StringIO

import pandas as pd
import plotly.express as px
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_table as dt
from PIL import Image
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_table.Format import Format, Scheme, Group
from econuy.utils import sqlutil
from econuy.core import Pipeline
from econuy.transform import chg_diff, convert_usd, convert_real, convert_gdp, resample, rolling, rebase, decompose
from flask import current_app

from econuy_web.dash_apps.querystrings import encode_state, parse_state
from econuy_web.dash_apps.visualization.components import build_layout
from econuy_web.dash_apps.visualization import utils


def register_general_callbacks(app):

    from econuy_web import db

    @app.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
    def toggle_navbar_collapse(n, is_open):
        if n:
            return not is_open
        return is_open

    def tabs_components(i: int):
        id_values = [(f"table-{i}", "value"),
                     (f"indicator-{i}", "value"),
                     (f"usd-switch-{i}", "on"),
                     (f"real-switch-{i}", "on"),
                     (f"order-{i}", "value"),
                     (f"real-dates-{i}", "start_date"),
                     (f"real-dates-{i}", "end_date"),
                     (f"gdp-switch-{i}", "on"),
                     (f"resample-switch-{i}", "on"),
                     (f"resample-freq-{i}", "value"),
                     (f"resample-operation-{i}", "value"),
                     (f"rolling-switch-{i}", "on"),
                     (f"rolling-periods-{i}", "value"),
                     (f"rolling-operation-{i}", "value"),
                     (f"chg-diff-switch-{i}", "on"),
                     (f"chg-diff-operation-{i}", "value"),
                     (f"chg-diff-period-{i}", "value"),
                     (f"rebase-switch-{i}", "on"),
                     (f"rebase-dates-{i}", "start_date"),
                     (f"rebase-dates-{i}", "end_date"),
                     (f"rebase-base-{i}", "value"),
                     (f"decompose-switch-{i}", "on"),
                     (f"decompose-method-{i}", "value"),
                     (f"decompose-component-{i}", "value"),
                     ]
        return id_values

    id_values_stacked = [tabs_components(i) for i in range(1, 4)]
    id_values = ([item for sublist in id_values_stacked for item in sublist]
                 + [("chart-type", "value"),
                     ("chart-dates", "start_date"),
                     ("chart-dates", "end_date"),
                     ("chart-title", "value"),
                     ("chart-subtitle", "value")])
    zipped_id_values = list(zip(*id_values))

    @app.callback(
        Output("url", "search"),
        [Input(id, param) for (id, param) in id_values])
    def update_url_state(*values):
        """
        When any of the (id, param) values changes, this callback gets triggered.

        Passes the list of component id's, the list of component parameters
        (zipped together in component_ids_zipped), and the value to encode_state()
        and return a properly formed querystring.
        """
        return encode_state(zipped_id_values, values)

    @app.callback(
        Output("page-layout", "children"),
        [Input("url", "href")])
    def page_load(href):
        """
        Upon page load, take the url, parse the querystring, and use the
        resulting state dictionary to build up the layout.
        """
        if not href:
            return []
        state = parse_state(href)
        return build_layout(state)

    @app.callback(
        [Output("collapse", "is_open"),
         Output("collapse-button", "children")],
        [Input("collapse-button", "n_clicks")],
        [State("collapse", "is_open"),
         State("collapse-button", "children")])
    def collapse_forms(n, is_open, text):
        if not n:
            return True, text
        if text == "Mostrar selección":
            text = "Ocultar selección"
        else:
            text = "Mostrar selección"
        return not is_open, text

    @app.callback(
        [Output("metadata-collapse", "is_open"),
         Output("metadata-button", "children")],
        [Input("metadata-button", "n_clicks")],
        [State("metadata-collapse", "is_open"),
         State("metadata-button", "children")])
    def collapse_metadata(n, is_open, text):
        if not n:
            return False, text
        if text == "Mostrar metadatos":
            text = "Ocultar metadatos"
        else:
            text = "Mostrar metadatos"
        return not is_open, text


    @app.callback(
        [Output("final-data", "data"),
         Output("final-metadata", "data"),
         Output("csv-button", "disabled"),
         Output("xlsx-button", "disabled"),
         Output("metadata-button", "disabled"),
         Output("metadata-collapse", "children")],
        [Input(f"data-transformed-{i}", "data") for i in range(1, 4)]
        + [Input(f"metadata-transformed-{i}", "data") for i in range(1, 4)],
        [State(f"table-{i}", "value") for i in range(1, 4)]
        + [State(f"indicator-{i}", "value") for i in range(1, 4)])
    def build_final_df_and_metadata(*args):
        data_records = args[:3]
        metadata_records = args[3:6]
        tables = args[6:9]
        indicators = args[9:]
        dfs = []
        for data_record, metadata_record, table, indicator in zip(data_records, metadata_records,
                                                                  tables, indicators):
            if not table or not indicator:
                continue
            if data_record:
                transformed = pd.DataFrame.from_records(data_record,
                                                        coerce_float=True, index="index")
                transformed.index = pd.to_datetime(transformed.index)
                metadata = pd.DataFrame.from_records(metadata_record)
                transformed.columns = pd.MultiIndex.from_frame(metadata)
                dfs.append(transformed)
        if len(dfs) == 0:
            return {}, {}, True, True, True, []
        dfs = [df for df in dfs if df is not None]
        tables = [table for table in tables if table is not None]
        tables_dedup = utils.dedup_colnames(dfs=dfs, tables=tables)
        final_data = utils.concat(dfs=tables_dedup)
        final_data.dropna(how="all", inplace=True)

        final_metadata = final_data.columns.to_frame()
        final_data.columns = final_data.columns.get_level_values(0)
        final_data.reset_index(inplace=True)
        collapse_metadata = dbc.Card(dbc.CardBody(
            dbc.Table.from_dataframe(final_metadata.T, responsive=True,
                                     striped=True, bordered=True, header=False,
                                     index=True, size="sm")), style={"fontSize": "12px"})

        return final_data.to_dict("records"), final_metadata.to_dict("records"), False, False, False, collapse_metadata

    @app.callback(
        [Output("graph-spinner", "children"),
         Output("html-div", "children"),
         Output("clipboard", "className")],
        [Input("final-data", "data"),
         Input("final-metadata", "data"),
         Input("chart-title", "value"),
         Input("chart-subtitle", "value"),
         Input("chart-dates", "start_date"),
         Input("chart-dates", "end_date"),
         Input("chart-type", "value")] +
        [Input(f"table-{i}", "value") for i in range(1, 4)] +
        [Input(f"indicator-{i}", "value") for i in range(1, 4)])
    def update_chart(final_data_record, final_metadata_record, title, subtitle,
                     start_date, end_date, chart_type, *tables_indicators):
        if not final_data_record:
            return dcc.Graph(id="graph"), "", "d-inline btn btn-primary disabled"
        data = pd.DataFrame.from_records(final_data_record, coerce_float=True, index="index")
        final_metadata = pd.DataFrame.from_records(final_metadata_record)
        data.index = pd.to_datetime(data.index)
        start_date = start_date or "1970-01-01"
        end_date = end_date or "2100-01-01"
        data = data.loc[(data.index >= start_date) & (data.index <= end_date), :]
        if len(data) > 7000:
            data = resample(data, rule="M", operation="mean")

        tables = tables_indicators[:3]
        indicators = tables_indicators[3:]
        tables = [table for table, indicator in zip(tables, indicators) if indicator]
        labels = utils.get_labels(tables)
        labels_dedup = list(dict.fromkeys(labels))
        if not title:
            title = "<br>".join(labels_dedup)
        if subtitle:
            title = f"{title}<br><span style='font-size: 14px'>{subtitle}</span>"
        height = 600 + 20 * len(labels_dedup)
        if chart_type != "table":
            if chart_type == "bar":
                fig = px.bar(data, y=data.columns,
                                height=height, title=title,
                                color_discrete_sequence=px.colors.qualitative.Bold,
                                barmode="group", )
            elif chart_type == "stackbar":
                fig = px.bar(data, y=data.columns,
                                height=height, title=title,
                                color_discrete_sequence=px.colors.qualitative.Bold,
                                barmode="stack", )
            elif chart_type == "area":
                fig = px.area(data, y=data.columns,
                                height=height, title=title,
                                color_discrete_sequence=px.colors.qualitative.Bold,
                                )
            elif chart_type == "normarea":
                fig = px.area(data, y=data.columns,
                                height=height, title=title,
                                color_discrete_sequence=px.colors.qualitative.Bold,
                                groupnorm="fraction")
            elif chart_type == "lineyears":
                aux = data.copy()
                aux["Año"] = aux.index.year
                if pd.infer_freq(aux.index) in ["M", "MS", "Q", "Q-DEC"]:
                    aux["Período"] = aux.index.month_name()
                elif pd.infer_freq(aux.index) in ["A", "A-DEC"]:
                    raise PreventUpdate
                elif pd.infer_freq(aux.index) in ["W", "W-SUN"]:
                    aux["Período"] = aux.index.strftime("%U").astype("int32")
                else:
                    aux["Período"] = aux.index.dayofyear
                fig = px.line(aux, y=aux.columns, color="Año", x="Período",
                                height=height, title=title,
                                color_discrete_sequence=px.colors.qualitative.Bold,
                                )
            else:
                fig = px.line(data, y=data.columns,
                                height=height, title=title,
                                color_discrete_sequence=px.colors.qualitative.Bold,
                                )
            ylabels = []
            for currency, unit, inf in zip(
                    final_metadata["Moneda"],
                    final_metadata["Unidad"],
                    final_metadata["Inf. adj."]):
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
            fig.update_layout({"margin": {"l": 20, "r": 20},
                                "legend": {"orientation": "h", "yanchor": "top",
                                            "y": -0.1, "xanchor": "left",
                                            "x": 0},
                                "legend_orientation": "h",
                                "xaxis_title": "",
                                "yaxis_title": ylabels,
                                "legend_title": "",
                                "title": {"y": 0.9,
                                        "yanchor": "top",
                                        "font": {"size": 16}}})
            path_to_logo = path.join(current_app.root_path,
                                        "static", "cards.jpg")
            fig.add_layout_image(dict(source=Image.open(path_to_logo),
                                        sizex=0.1, sizey=0.1, xanchor="right",
                                        yanchor="bottom", xref="paper",
                                        yref="paper",
                                        x=1, y=1.01))
            # fig.update_xaxes(
            #     rangeselector=dict(yanchor="bottom", y=1.01, xanchor="right",
            #                         x=0.9,
            #                         buttons=list([
            #                             dict(count=1, label="1m", step="month",
            #                                 stepmode="backward"),
            #                             dict(count=6, label="6m", step="month",
            #                                 stepmode="backward"),
            #                             dict(count=1, label="YTD", step="year",
            #                                 stepmode="todate"),
            #                             dict(count=1, label="1a", step="year",
            #                                 stepmode="backward"),
            #                             dict(count=5, label="5a", step="year",
            #                                 stepmode="backward"),
            #                             dict(label="todos", step="all")])))
            html_string = StringIO()
            fig.write_html(html_string)
            html_string.seek(0)
            viz = dcc.Graph(figure=fig, id="graph", config={"displayModeBar": False})
            return viz, html_string.read(), "d-inline btn btn-primary"
        else:
            data.reset_index(inplace=True)
            data.rename(columns={"index": "Fecha"}, inplace=True)
            data["Fecha"] = data["Fecha"].dt.strftime("%d-%m-%Y")
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
                                                  data.columns[1:]],
                                         data=data.to_dict("records"),
                                         style_cell={"textAlign": "center"},
                                         style_header={
                                             "whiteSpace": "normal",
                                             "height": "auto",
                                             "textAlign": "center"},
                                         page_action="none",
                                         fixed_rows={"headers": True})])
            return viz, [], "d-inline btn btn-primary disabled"

    @app.callback(
        Output("download-data-csv", "data"),
        [Input("csv-button", "n_clicks")],
        [State("final-data", "data"),
         State("final-metadata", "data")], prevent_initial_call=True)
    def download_csv(n, final_data_record, final_metadata_record):
        if not final_data_record:
            raise PreventUpdate
        data = pd.DataFrame.from_records(final_data_record, coerce_float=True, index="index")
        final_metadata = pd.DataFrame.from_records(final_metadata_record)
        data.index = pd.to_datetime(data.index)
        data.columns = pd.MultiIndex.from_frame(final_metadata)
        data.rename_axis(None, axis=0, inplace=True)
        return dcc.send_bytes(str.encode(data.to_csv(), encoding="latin1"), "econuy-data.csv")

    @app.callback(
        Output("download-data-xlsx", "data"),
        [Input("xlsx-button", "n_clicks")],
        [State("final-data", "data"),
         State("final-metadata", "data")], prevent_initial_call=True)
    def download_xlsx(n, final_data_record, final_metadata_record):
        if not final_data_record:
            raise PreventUpdate
        data = pd.DataFrame.from_records(final_data_record, coerce_float=True, index="index")
        final_metadata = pd.DataFrame.from_records(final_metadata_record)
        data.index = pd.to_datetime(data.index)
        data.columns = pd.MultiIndex.from_frame(final_metadata)
        data.rename_axis(None, axis=0, inplace=True)
        return dcc.send_bytes(data.to_excel, "econuy-data.xlsx")


def register_tabs_callbacks(app, i: int):

    from econuy_web import db

    @app.callback(
        [Output(f"indicator-{i}", "options"),
         Output(f"indicator-{i}", "disabled")],
        [Input(f"table-{i}", "value")])
    def indicator_options(table):
        if not table:
            raise PreventUpdate
        df = sqlutil.read(con=db.engine, table_name=table)
        columns = df.columns.get_level_values(0)
        return ([{"label": "Todos los indicadores", "value": "*"}]
                + [{"label": v, "value": v} for v in columns]), False

    @app.callback(
        [Output(f"order-{i}", "options"),
         Output(f"order-{i}", "disabled"),
         Output(f"order-{i}", "value")],
        [Input(f"usd-switch-{i}", "on"),
         Input(f"real-switch-{i}", "on"),
         Input(f"gdp-switch-{i}", "on"),
         Input(f"resample-switch-{i}", "on"),
         Input(f"rolling-switch-{i}", "on"),
         Input(f"chg-diff-switch-{i}", "on"),
         Input(f"rebase-switch-{i}", "on"),
         Input(f"decompose-switch-{i}", "on")],
        [State(f"order-{i}", "value")])
    def transformation_order(usd, real, gdp, resample, rolling, chg_diff, rebase, decompose,
                             current_values):
        transformations = {"usd": [usd, "Convertir a dólares"],
                           "real": [real, "Convertir a precios constantes"],
                           "gdp": [gdp, "Convertir a % del PBI"],
                           "resample": [resample, "Cambiar frecuencia"],
                           "rolling": [rolling, "Acumular"],
                           "chg-diff": [chg_diff, "Calcular variaciones o diferencias"],
                           "rebase": [rebase, "Indexar a período base"],
                           "decompose": [decompose, "Desestacionalizar"]}
        transformations_on = [{"label": v[1], "value": k} for k, v in transformations.items()
                                  if v[0] is True or v[0] == "True"]
        transformations_off = [{"label": v[1], "value": k} for k, v in transformations.items()
                                  if v[0] is False or v[0] == "False"]
        selected_values = [option["value"] for option in transformations_on]
        unselected_values = [option["value"] for option in transformations_off]
        current_values = current_values or []
        new_values = current_values + selected_values
        new_values = [x for x in new_values if x not in unselected_values]
        new_values_dedup = list(dict.fromkeys(new_values))
        return transformations_on, False, new_values_dedup

    @app.callback(
        [Output(f"data-{i}", "data"),
         Output(f"metadata-{i}", "data")],
        [Input(f"table-{i}", "value"),
         Input(f"indicator-{i}", "value")])
    def store_query_data(table, indicator):
        if not table or not indicator:
            return {}, {}
        if "*" in indicator:
            indicator = "*"
        data = sqlutil.read(con=db.engine, table_name=table, cols=indicator)
        metadata = data.columns.to_frame()
        data.columns = data.columns.get_level_values(0)
        data.reset_index(inplace=True)
        return data.to_dict("records"), metadata.to_dict("records")

    @app.callback(
        [Output(f"data-transformed-{i}", "data"),
         Output(f"metadata-transformed-{i}", "data")],
        [Input(f"real-dates-{i}", "start_date"),
         Input(f"real-dates-{i}", "end_date"),
         Input(f"resample-freq-{i}", "value"),
         Input(f"resample-operation-{i}", "value"),
         Input(f"rolling-periods-{i}", "value"),
         Input(f"rolling-operation-{i}", "value"),
         Input(f"chg-diff-operation-{i}", "value"),
         Input(f"chg-diff-period-{i}", "value"),
         Input(f"rebase-dates-{i}", "start_date"),
         Input(f"rebase-dates-{i}", "end_date"),
         Input(f"rebase-base-{i}", "value"),
         Input(f"decompose-method-{i}", "value"),
         Input(f"decompose-component-{i}", "value"),
         Input(f"order-{i}", "value"),
         Input(f"data-{i}", "data"),
         Input(f"metadata-{i}", "data")])
    def store_transformed_data(real_start, real_end, resample_freq, resample_operation,
                               rolling_periods, rolling_operation, chg_diff_operation,
                               chg_diff_period, rebase_start, rebase_end, rebase_base,
                               decompose_method, decompose_component,
                               order, query_data, query_metadata):
        if not order:
            return query_data, query_metadata
        if not query_data:
            return {}, {}
        if (("resample" in order and (not resample_freq or not resample_operation))
            or ("rolling" in order and (not rolling_periods or not rolling_operation))
            or ("chg-diff" in order and (not chg_diff_operation or not chg_diff_period))
            or ("rebase" in order and (not rebase_start or not rebase_base))
            or ("decompose" in order and (not decompose_method or not decompose_component))):
            raise PreventUpdate
        data = pd.DataFrame.from_records(query_data, coerce_float=True, index="index")
        data.index = pd.to_datetime(data.index)
        metadata = pd.DataFrame.from_records(query_metadata)
        data.columns = pd.MultiIndex.from_frame(metadata)
        p = Pipeline(location=db.engine, download=False)

        transformations = {"usd": lambda x: convert_usd(x, pipeline=p, errors="ignore"),
                           "real": lambda x: convert_real(x, start_date=real_start,
                                                          end_date=real_end, pipeline=p,
                                                          errors="ignore"),
                           "gdp": lambda x: convert_gdp(x, pipeline=p, errors="ignore"),
                           "resample": lambda x: resample(x, rule=resample_freq,
                                                          operation=resample_operation),
                           "rolling": lambda x: rolling(x, window=rolling_periods,
                                                        operation=rolling_operation),
                           "chg-diff": lambda x: chg_diff(x, operation=chg_diff_operation,
                                                          period=chg_diff_period),
                           "rebase": lambda x: rebase(x, start_date=rebase_start,
                                                      end_date=rebase_end, base=rebase_base),
                           "decompose": lambda x: decompose(x, component=decompose_component,
                                                            method=decompose_method,
                                                            force_x13=True, errors="ignore")}
        transformed_data = data.copy()
        for t in order:
            transformed_data = transformations[t](transformed_data)

        transformed_metadata = transformed_data.columns.to_frame()
        transformed_data.columns = transformed_data.columns.get_level_values(0)
        transformed_data.reset_index(inplace=True)

        return transformed_data.to_dict("records"), transformed_metadata.to_dict("records")
