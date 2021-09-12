import datetime as dt

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

NAVBAR = dbc.Navbar(
            [html.A(
                dbc.Row([
                    dbc.Col(html.Img(src="assets/logo_only.png", height="40px")),
                    dbc.Col(dbc.NavbarBrand("econuy", className="ml-2"))]),
                href="/"),
             dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
             dbc.Collapse(dbc.Row(
                 dbc.Nav([
                     dbc.DropdownMenu([dbc.DropdownMenuItem("2015",
                                                            href="/over2/?dates=start_date&dates=2015-01-01", external_link=True),
                                       dbc.DropdownMenuItem("2019", href="/over2/?dates=start_date&dates=2019-01-01", external_link=True)],
                                      nav=True, in_navbar=True, label="Monitor"),
                     dbc.NavItem(dbc.NavLink("Visualizador", href="/v/", external_link=True)),
                     dbc.NavItem(dbc.NavLink("Docs Python", href="https://econuy.readthedocs.io/", external_link=True)),
                     dbc.NavItem(dbc.NavLink("Inicio", href="/", external_link=True))
                     ]),
                 no_gutters=True,
                 className="ml-auto flex-nowrap mt-3 mt-md-0",
                 align="center"),
                          id="navbar-collapse", navbar=True, is_open=False
                          )
             ]
            )

FOOTER = dbc.Row(
    dbc.Col(
        html.Footer(f"Rafael Xavier, {dt.date.today().year}", className="text-muted text-center")),
    justify="center", className="mx-0 mx-md-3 mb-2")