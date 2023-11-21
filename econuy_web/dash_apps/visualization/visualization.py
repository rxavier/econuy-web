import plotly.io as pio
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash import Dash

from econuy_web.dash_apps.visualization.callbacks import (
    register_general_callbacks,
    register_tabs_callbacks,
)

pio.templates.default = "plotly_white"


def add_dash(server):
    app = Dash(
        server=server,
        url_base_pathname="/interactive/",
        suppress_callback_exceptions=True,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            "https://fonts.googleapis.com/css2?family=Montserrat&family=Roboto&display=swap",
        ],
        title="Visualización interactiva",
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        ],
    )
    app.layout = html.Div(
        [
            dcc.Location(id="url", refresh=False),
            html.Div(id="page-layout"),
        ]
    )

    register_general_callbacks(app)

    for i in range(1, 4):
        register_tabs_callbacks(app, i=i)

    return app.server
