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
                            className="dash-bootstrap", display_format="DD-MM-YYYY", start_date="2010-01-01"),
                        md=4),
                className="mx-0 mx-md-3", justify="center"),
        html.Br(),
        dbc.Tabs([
            dbc.Tab(tab_activity, label="Actividad", activeLabelClassName="btn btn-primary"),
            dbc.Tab(tab_prices, label="Precios", activeLabelClassName="btn btn-primary"),
            dbc.Tab(tab_fiscal, label="Fiscal", activeLabelClassName="btn btn-primary"),
            dbc.Tab(tab_labor, label="Laboral", activeLabelClassName="btn btn-primary"),
            dbc.Tab(tab_external, label="Externo", activeLabelClassName="btn btn-primary")
        ], className="mx-0 mx-md-3 nav-justified"),
        FOOTER
        ])

tab_activity = [dbc.Row([
    dbc.Col(dcc.Graph(id="chart-gdp", config={"displayModeBar": False}), md=6),
    dbc.Col(dcc.Graph(id="chart-industrial", config={"displayModeBar": False}), md=6)
]),
                dbc.Row([
    dbc.Col(dcc.Graph(id="chart-demand", config={"displayModeBar": False}), md=6),
    dbc.Col(dcc.Graph(id="chart-supply", config={"displayModeBar": False}), md=6)
])]

tab_prices = [dbc.Row([
    dbc.Col(dcc.Graph(id="chart-inflation", config={"displayModeBar": False}), md=6),
    dbc.Col(dcc.Graph(id="chart-inflation-measures", config={"displayModeBar": False}), md=6)
]),
              dbc.Row(dbc.Col(dcc.Graph(id="chart-nxr", config={"displayModeBar": False}), md=6))]

tab_fiscal = [dbc.Row([
    dbc.Col(dcc.Graph(id="chart-primary-global", config={"displayModeBar": False}), md=6),
    dbc.Col(dcc.Graph(id="chart-balance-sectors", config={"displayModeBar": False}), md=6)
]),
              dbc.Row([
    dbc.Col(dcc.Graph(id="chart-revenue", config={"displayModeBar": False}), md=6),
    dbc.Col(dcc.Graph(id="chart-debt", config={"displayModeBar": False}), md=6)
])]

tab_labor = [dbc.Row([
    dbc.Col(dcc.Graph(id="chart-activity-employment", config={"displayModeBar": False}), md=6),
    dbc.Col(dcc.Graph(id="chart-unemployment", config={"displayModeBar": False}), md=6)
]),
              dbc.Row([
    dbc.Col(dcc.Graph(id="chart-real-wages", config={"displayModeBar": False}), md=6)
])]

tab_external = [dbc.Row([
    dbc.Col(dcc.Graph(id="chart-exp-imp", config={"displayModeBar": False}), md=6),
    dbc.Col(dcc.Graph(id="chart-tot", config={"displayModeBar": False}), md=6)
]),
              dbc.Row([
    dbc.Col(dcc.Graph(id="chart-rxr", config={"displayModeBar": False}), md=6),
    dbc.Col(dcc.Graph(id="chart-commodity-index", config={"displayModeBar": False}), md=6)
])]