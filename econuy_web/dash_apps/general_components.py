import datetime as dt

import dash_bootstrap_components as dbc
from dash import html

NAVBAR = dbc.Navbar(
    [
        html.A(
            dbc.Row(
                [
                    dbc.Col(html.Img(src="assets/logo_only.png", height="40px")),
                    dbc.Col(dbc.NavbarBrand("econuy", className="ml-2")),
                ]
            ),
            href="/",
        ),
        dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
        dbc.Collapse(
            dbc.Row(
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Monitor", href="/monitor/", external_link=True)),
                        dbc.NavItem(
                            dbc.NavLink("Interactivo", href="/interactive/", external_link=True)
                        ),
                        dbc.NavItem(dbc.NavLink("Inicio", href="/", external_link=True)),
                    ]
                ),
                className="ml-auto flex-nowrap mt-3 mt-md-0",
                align="center",
            ),
            id="navbar-collapse",
            navbar=True,
            is_open=False,
        ),
    ]
)

FOOTER = html.Div(
    [
        html.Hr(className="mx-0 mx-md-3"),
        dbc.Row(
            dbc.Col(
                html.Footer(
                    f"Rafael Xavier, {dt.date.today().year}",
                    className="text-muted text-center",
                )
            ),
            justify="center",
            className="mx-0 mx-md-3 mb-2",
        ),
    ]
)
