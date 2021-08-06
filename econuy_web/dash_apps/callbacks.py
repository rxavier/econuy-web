from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from econuy.utils import sqlutil

from econuy_web.dash_apps.querystrings import encode_state, parse_state
from econuy_web.dash_apps.components import build_layout


def register_general_callbacks(app):

    @app.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")],
    )
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
                     #(f"order-{i}", "options")
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
         Input(f"real-switch-{i}", "on")],
        [State(f"order-{i}", "value")])
    def transformation_order(usd, real, current_values):
        transformations = {"Convertir a dólares": usd,
                           "Deflactar": real}
        transformations_parsed = [{"label": k, "value": k} for k, v in transformations.items()
                                  if v is True or v=="True"]
        selected_values = [option["value"] for option in transformations_parsed]
        current_values = current_values or []
        new_values = current_values + selected_values
        new_values_dedup = list(dict.fromkeys(new_values))
        return transformations_parsed, False, new_values_dedup

