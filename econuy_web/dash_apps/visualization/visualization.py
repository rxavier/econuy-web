import plotly.io as pio
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash import Dash

from econuy_web.dash_apps.visualization.callbacks import register_general_callbacks, register_tabs_callbacks

pio.templates.default = "plotly_white"

def add_dash(server):
    app = Dash(server=server, url_base_pathname="/v/", suppress_callback_exceptions=True,
               external_stylesheets=[dbc.themes.BOOTSTRAP],
               meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ])
    app.layout = html.Div([
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-layout"),
    ])

    register_general_callbacks(app)

    for i in range(1, 4):
        register_tabs_callbacks(app, i=i)

    return app.server
