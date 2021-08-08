import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from econuy.utils import sqlutil
from econuy.core import Pipeline
from econuy.session import Session
from econuy.transform import convert_usd, convert_real, convert_gdp, resample

from econuy_web.dash_apps.querystrings import encode_state, parse_state
from econuy_web.dash_apps.components import build_layout


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
                     (f"resample-method-{i}", "value")
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
        Output("graph", "figure"),
        [Input(f"data-transformed-{i}", "data") for i in range(1, 4)]
        + [Input(f"metadata-transformed-{i}", "data") for i in range(1, 4)]
        + [Input(f"table-{i}", "value") for i in range(1, 4)])
    def update_chart(*args):
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
        s = Session()
        s._datasets = {name: dataset for name, dataset in zip(tables, dfs) if name}
        s.concat(select="all", concat_name="final")
        data = s.datasets["concat_final"]
        data.columns = data.columns.get_level_values(0)
        data.dropna(how="all", inplace=True)
        fig = px.line(data, y=data.columns,
                      color_discrete_sequence=px.colors.qualitative.Vivid,
                      template="plotly_white")
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
         Input(f"resample-switch-{i}", "on")],
        [State(f"order-{i}", "value")])
    def transformation_order(usd, real, gdp, resample, current_values):
        transformations = {"usd": [usd, "Convertir a dólares"],
                           "real": [real, "Convertir a precios constantes"],
                           "gdp": [gdp, "Convertir a % del PBI"],
                           "resample": [resample, "Cambiar frecuencia"]}
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
         Input(f"resample-method-{i}", "value"),
         Input(f"order-{i}", "value"),
         Input(f"data-{i}", "data"),
         Input(f"metadata-{i}", "data")])
    def store_transformed_data(real_start, real_end, resample_freq, resample_method,
                               order, query_data, query_metadata):
        if not order:
            return query_data, query_metadata
        if ("resample" in order and (not resample_freq or not resample_method)):
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
                                                          operation=resample_method)}
        transformed_data = data.copy()
        for t in order:
            transformed_data = transformations[t](transformed_data)

        transformed_metadata = transformed_data.columns.to_frame()
        transformed_data.columns = transformed_data.columns.get_level_values(0)
        transformed_data.reset_index(inplace=True)

        return transformed_data.to_dict("records"), transformed_metadata.to_dict("records")
