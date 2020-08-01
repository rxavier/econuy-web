from typing import Dict

from dash import Dash
from dash.dependencies import Input, Output, State, ALL
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd

from econuy import transform
from econuy.utils import sqlutil
from econuy.app.app_strings import table_options

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

url_base = '/dash/app/'


def add_dash(server, options):
    app = Dash(server=server, url_base_pathname=url_base,
               external_stylesheets=external_stylesheets)
    app.layout = html.Div([html.H1("Visualizador econuy"),
                           html.Button("Agregar indicador", id="add-indicator",
                                       n_clicks=0),
                           html.Br(), html.Br(),
                           html.Div(id="dropdown-container",
                                    children=[]),
                           dcc.Graph(id="chart")])

    register_callbacks(app, options=options)

    return app.server


def register_callbacks(app, options):
    from econuy.app import db

    @app.callback(
        Output('chart', 'figure'),
        [Input({"type": 'indicator-dropdown', "index": ALL}, 'value'),
         Input({"type": 'usd-check', "index": ALL}, 'value'),
         Input({"type": 'real-check', "index": ALL}, 'value'),
         Input({"type": 'real-range', "index": ALL}, 'start_date'),
         Input({"type": 'real-range', "index": ALL}, 'end_date'),
         Input({"type": 'gdp-check', "index": ALL}, 'value'),
         Input({"type": "order-1", "index": ALL}, "value"),
         Input({"type": "order-2", "index": ALL}, "value"),
         Input({"type": "order-3", "index": ALL}, "value")])
    def update_df(indicators, usds, reals, reals_starts, reals_ends,
                  gdps, orders_1, orders_2, orders_3):
        dataframes = []
        labels = []
        for (indicator, usd, real,
             real_start, real_end, gdp, order_1, order_2, order_3) in zip(indicators,
                                                                 usds,
                                                                 reals,
                                                                 reals_starts,
                                                                 reals_ends,
                                                                 gdps,
                                                                 orders_1,
                                                                 orders_2,
                                                                 orders_3):
            if indicator is None:
                continue
            try:
                split = indicator.split("$")
                table = split[0]
                column = split[1]
                labels.append(column)
            except AttributeError:
                pass
            df_aux = sqlutil.read(con=db.engine, table_name=table, cols=column)
            df_aux.columns.set_levels(
                [f"{table_options[table]} | {column}"],
                level=0, inplace=True)
            submit_order = {"usd": order_1,
                            "real": order_2,
                            "gdp": order_3}
            all_transforms = {k: (True if True in v else False) for k, v
                              in
                              {"usd": usd, "real": real, "gdp": gdp}.items()}
            orders = define_order(submit_order, all_transforms)
            function_dict = {
                "usd": lambda x: transform.convert_usd(x, update_loc=db.engine,
                                                       only_get=True),
                "real": lambda x: transform.convert_real(
                    x, update_loc=db.engine, only_get=True,
                    start_date=real_start,
                    end_date=real_end),
                "gdp": lambda x: transform.convert_gdp(x, update_loc=db.engine,
                                                       only_get=True)
                }

            for t in orders.values():
                df_aux = function_dict[t](df_aux)
            dataframes.append(df_aux)

        if len(dataframes) == 0:
            return []
        df = pd.concat(dataframes, axis=1)

        fig = px.line(df, x=df.index,
                      y=list(df.columns.get_level_values(level=0)),
                      title="Visualizador econuy",
                      labels=labels)
        fig.update_layout({"legend_orientation": "h",
                           "xaxis_title": "",
                           "yaxis_title": "",
                           "legend_title": ""})
        return fig

    @app.callback(
        Output('dropdown-container', 'children'),
        [Input('add-indicator', 'n_clicks')],
        [State('dropdown-container', 'children')])
    def display_dropdowns(n_clicks, children, opts=options):
        indicator_dropdown = dcc.Dropdown(
            id={
                'type': 'indicator-dropdown',
                'index': n_clicks
            },
            options=opts, placeholder="Seleccionar indicador"
        )
        usd = html.Div(children=[
            html.Div(
                style={'display': 'inline-block', "vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    'type': 'usd-check',
                    'index': n_clicks},
                    options=[
                        {"label": "Convertir a dólares",
                         "value": True}], value=[])]),
            order_dropdown(number="1", n_clicks=n_clicks)])
        real = html.Div(children=[
            html.Div(
                style={'display': 'inline-block', "vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    'type': 'real-check',
                    'index': n_clicks
                }, options=[{"label": "Deflactar",
                             "value": True}], value=[])]),
            html.Div(style={'display': 'inline-block', 'margin-left': "10px",
                            "vertical-align": "middle"},
                     children=[dcc.DatePickerRange(id={
                         'type': 'real-range',
                         'index': n_clicks},
                         start_date_placeholder_text="Fecha inicial",
                         end_date_placeholder_text="Fecha final")]),
            order_dropdown(number="2", n_clicks=n_clicks)])
        gdp = html.Div(children=[
            html.Div(
                style={'display': 'inline-block', "vertical-align": "middle"},
                children=[dcc.Checklist(id={
                    'type': 'gdp-check',
                    'index': n_clicks},
                    options=[
                        {"label": "Calcular % PBI",
                         "value": True}], value=[])]),
            order_dropdown(number="3", n_clicks=n_clicks)])
        short_br = html.Div(style={"height": "5px"})
        children.extend(
            [indicator_dropdown, html.Br(), usd, short_br, real, short_br, gdp,
             html.Br()])
        return children


def order_dropdown(number: str, n_clicks):
    return html.Div(
        style={'display': 'inline-block', 'margin-left': "10px",
               "vertical-align": "middle"},
        children=[dcc.Dropdown(
            id={'type': f'order-{number}',
                'index': n_clicks},
            options=[{"label": str(i), "value":
                str(i)} for i in range(1, 9)],
            value="1")])


def define_order(submit_order, all_transforms):
    pruned_order = {k: v for k, v in submit_order.items()
                    if all_transforms[k] is True}
    aux = sorted(pruned_order, key=pruned_order.get)
    return dict(zip(list(range(len(aux))), aux))
