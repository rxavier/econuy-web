import re
import uuid
from PIL import Image
from os import path, mkdir
from io import BytesIO
from typing import List, Dict

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash
from dash.exceptions import PreventUpdate
from dash_table.Format import Format, Scheme, Group
from flask import (url_for, send_file, request, flash,
                   current_app, send_from_directory)
from sqlalchemy.exc import ProgrammingError
from econuy.core import Pipeline
from econuy import transform
from econuy.utils import sqlutil, metadata

from econuy_web.dash_apps.callbacks import register_general_callbacks, register_tabs_callbacks


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
