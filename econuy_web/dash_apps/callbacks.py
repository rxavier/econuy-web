import re

import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from econuy.utils import sqlutil
from econuy.core import Pipeline
from econuy.transform import chg_diff, convert_usd, convert_real, convert_gdp, resample, rolling, rebase, decompose

from econuy_web.dash_apps.querystrings import encode_state, parse_state
from econuy_web.dash_apps.components import build_layout
from econuy_web.dash_apps import utils


def register_general_callbacks(app):

    @app.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
    def toggle_navbar_collapse(n, is_open):
        if n:
            return not is_open
        return is_open

    def shareable_components(i: int):
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

    id_values_stacked = [shareable_components(i) for i in range(1, 4)]
    id_values = [item for sublist in id_values_stacked for item in sublist]
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
    def fade_forms(n, is_open, text):
        if not n:
            return True, text
        if text == "Mostrar selección":
            text = "Ocultar selección"
        else:
            text = "Mostrar selección"
        return not is_open, text

    @app.callback(
        [Output("final-data", "data"),
         Output("final-metadata", "data")],
        [Input(f"data-transformed-{i}", "data") for i in range(1, 4)]
        + [Input(f"metadata-transformed-{i}", "data") for i in range(1, 4)]
        + [Input(f"table-{i}", "value") for i in range(1, 4)])
    def build_final_df(*args):
        data_records = args[:3]
        metadata_records = args[3:6]
        tables = args[6:]
        dfs = []
        for data_record, metadata_record in zip(data_records, metadata_records):
            if data_record:
                transformed = pd.DataFrame.from_records(data_record,
                                                        coerce_float=True, index="index")
                transformed.index = pd.to_datetime(transformed.index)
                metadata = pd.DataFrame.from_records(metadata_record)
                transformed.columns = pd.MultiIndex.from_frame(metadata)
                dfs.append(transformed)
        if len(dfs) == 0:
            raise PreventUpdate
        dfs = [df for df in dfs if df is not None]
        tables = [table for table in tables if table is not None]
        tables_dedup = utils.dedup_colnames(dfs=dfs, tables=tables)
        final_data = utils.concat(dfs=tables_dedup)
        final_data.dropna(how="all", inplace=True)

        final_metadata = final_data.columns.to_frame()
        final_data.columns = final_data.columns.get_level_values(0)
        final_data.reset_index(inplace=True)

        return final_data.to_dict("records"), final_metadata.to_dict("records")

    @app.callback(
        Output("graph", "figure"),
        [Input("final-data", "data")] +
        [Input("final-metadata", "data")] +
        [Input(f"table-{i}", "value") for i in range(1, 4)] +
        [Input(f"indicator-{i}", "value") for i in range(1, 4)])
    def update_chart(final_data_record, final_metadata_record, *tables_indicators):
        data = pd.DataFrame.from_records(final_data_record, coerce_float=True, index="index")
        final_metadata = pd.DataFrame.from_records(final_metadata_record)
        data.index = pd.to_datetime(data.index)
        if len(data) > 7000:
            data = resample(data, rule="M", operation="mean")
        tables = tables_indicators[:3]
        indicators = tables_indicators[3:]
        tables = [table for table, indicator in zip(tables, indicators) if indicator]
        labels = utils.get_labels(tables)
        labels_dedup = list(dict.fromkeys(labels))
        title = "<br>".join(labels_dedup)
        height = 600 + 20 * len(labels_dedup)
        fig = px.line(data, y=data.columns,
                      color_discrete_sequence=px.colors.qualitative.Pastel,
                      template="plotly_white", title=title, height=height)
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
                                      "font": {"size": 20}}})
        return fig

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
