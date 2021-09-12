import datetime as dt

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from econuy_web.dash_apps.querystrings import apply_qs
from econuy_web.dash_apps.general_components import NAVBAR, FOOTER


def build_layout(params):
    from econuy_web.dash_apps.monitor.callbacks import load_datasets
    return html.Div([
        load_datasets(),
        NAVBAR,
        dbc.Row(
            dbc.Col([
                html.H1("Monitor", className="mt-2"),
                ]), className="mx-0 mx-md-3"),
        html.Br(),
        dbc.Row(dbc.Col(apply_qs(params)(dcc.DatePickerRange)(id="dates", start_date_placeholder_text="Inicio",
                            end_date_placeholder_text="Fin", clearable=True,
                            className="dash-bootstrap", display_format="DD-MM-YYYY", start_date="2010-01-01")),
                className="mx-0 mx-md-3"),
        html.Br(),
        dbc.Tabs([
            dbc.Tab(tab_activity, label="Actividad económica"),
            dbc.Tab(tab_prices, label="Precios"),
            dbc.Tab(tab_fiscal, label="Fiscal"),
            dbc.Tab(tab_laboral, label="Mercado laboral")
        ], className="mx-0 mx-md-3"),
        FOOTER
        ])

tab_activity = [dbc.Row([
    dbc.Col(dcc.Graph(id="chart-gdp"), md=6),
    dbc.Col(dcc.Graph(id="chart-industrial"), md=6)
]),
                dbc.Row([
    dbc.Col(dcc.Graph(id="chart-demand"), md=6),
    dbc.Col(dcc.Graph(id="chart-supply"), md=6)
])]

tab_prices = [dbc.Row([
    dbc.Col(dcc.Graph(id="chart-inflation"), md=6),
    dbc.Col(dcc.Graph(id="chart-inflation-measures"), md=6)
]),
              dbc.Row(dbc.Col(dcc.Graph(id="chart-nxr"), md=6))]

tab_fiscal = [dbc.Row([
    dbc.Col(dcc.Graph(id="chart-primary-global"), md=6),
    dbc.Col(dcc.Graph(id="chart-balance-sectors"), md=6)
]),
              dbc.Row([
    dbc.Col(dcc.Graph(id="chart-revenue"), md=6),
    dbc.Col(dcc.Graph(id="chart-debt"), md=6)
])]

tab_laboral = [dbc.Row([
    dbc.Col(dcc.Graph(id="chart-activity-employment"), md=6),
    dbc.Col(dcc.Graph(id="chart-unemployment"), md=6)
]),
              dbc.Row([
    dbc.Col(dcc.Graph(id="chart-real-wages"), md=6)
])]