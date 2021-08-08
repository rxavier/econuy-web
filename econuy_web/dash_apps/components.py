import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq

from econuy_web.app_strings import table_options
from econuy_web.dash_apps.querystrings import apply_qs


def build_layout(params):
    return html.Div([
        NAVBAR,
        dbc.Row(
            dbc.Col([
                html.H1("Visualizador", className="mt-2"),
                dbc.Button("Esconder selección", id="collapse-button", size="sm",
                           color="secondary", className="float-right mb-0 ml-0"),
                dbc.Collapse(form_tabs(params), id="collapse", is_open=True),
                ]), className="mx-0 mx-md-3"),
        dbc.Row(
            dbc.Col(dbc.Spinner(dcc.Graph(id="graph"), color="primary")))])


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


def form_builder(i: int, params):
    table_indicator = dbc.Card([
        dbc.CardHeader(html.H6("Seleccionar indicadores")),
        dbc.CardBody(
            dbc.Row([
                dbc.Col(
                    html.Div(
                    apply_qs(params)(dcc.Dropdown)(id=f"table-{i}",
                                 options=[{"label": v, "value": k} if "-----" not in v
                                          else {"label": v, "value": k, "disabled": True}
                                          for k, v in table_options.items()],
                                 placeholder="Seleccionar cuadro", optionHeight=50),
                    className="dash-bootstrap"), md=6),
                dbc.Col(dbc.Spinner(
                    html.Div(
                    apply_qs(params)(dcc.Dropdown)(id=f"indicator-{i}",
                                 options=[{"label": v, "value": k} if "-----" not in v
                                          else {"label": v, "value": k, "disabled": True}
                                          for k, v in table_options.items()],
                                 placeholder="Seleccionar indicadores", optionHeight=50,
                                 multi=True, disabled=True),
                    className="dash-bootstrap"), color="primary"), md=6)
                ]))
        ])

    first_form = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(
                    dbc.Row([
                        dbc.Col(html.H6("Convertir a dólares")),
                        dbc.Col(apply_qs(params)(daq.BooleanSwitch)(id=f"usd-switch-{i}",
                                                                    color="#0275d8"),
                                className="ml-auto")
                        ]), id=f"usd-header-{i}"
                    ),
                ], color="primary", outline=True, className="mb-0 mb-md-2"),
            dbc.Card([
                    dbc.CardHeader(
                        dbc.Row([
                            dbc.Col(html.H6("Convertir a % del PBI")),
                            dbc.Col(apply_qs(params)(daq.BooleanSwitch)(id=f"gdp-switch-{i}",
                                                                        color="#0275d8"),
                                    className="ml-auto")
                            ]), id=f"gdp-header-{i}"
                        ),
                    ], color="primary", outline=True)]
            , md=6),

        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    dbc.Row([
                        dbc.Col(html.H6("Convertir a precios constantes")),
                        dbc.Col(apply_qs(params)(daq.BooleanSwitch)(id=f"real-switch-{i}",
                                                                    color="#0275d8"),
                                className="ml-auto")
                        ]), id=f"real-header-{i}"
                    ),
                dbc.CardBody([dbc.Form(
                    dbc.FormGroup([
                        dbc.Label("Rango de fechas", html_for=f"real-dates-{i}", className="mr-2"),
                        apply_qs(params)(dcc.DatePickerRange)(start_date_placeholder_text="Inicial",
                                    end_date_placeholder_text="Final",
                                    display_format="DD-MM-YYYY", clearable=True,
                                    className="dash-bootstrap", id=f"real-dates-{i}"),
                        dbc.FormText("Las fechas definen el nivel de precios de referencia")
                        ]), id=f"real-dates-group-{i}")
                    ])
                ], color="primary", outline=True), md=6)
        ], form=True, className="mb-0 mb-md-2")

    second_form = dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    dbc.Row([
                        dbc.Col(html.H6("Cambiar frecuencia")),
                        dbc.Col(apply_qs(params)(daq.BooleanSwitch)(id=f"resample-switch-{i}",
                                                                    color="#0275d8"),
                                className="ml-auto")
                        ]), id=f"resample-header-{i}"
                    ),
                dbc.CardBody(dbc.Form([
                    dbc.FormGroup([
                        dbc.Label("Frecuencia"),
                        html.Div(apply_qs(params)(
                            dcc.Dropdown)(id=f"resample-freq-{i}",
                                          options=[{"label": "Anual", "value": "A-DEC"},
                                                   {"label": "Trimestral", "value": "Q-DEC"},
                                                   {"label": "Mensual", "value": "M"},
                                                   {"label": "14 días", "value": "2W"},
                                                   {"label": "Semanal", "value": "W"}],
                                          placeholder="Seleccionar frecuencia", searchable=False),
                            className="dash-bootstrap")]),
                    dbc.FormGroup([
                        dbc.Label("Método de agregación"),
                        html.Div(apply_qs(params)(
                            dcc.Dropdown)(id=f"resample-method-{i}",
                                          options=[{"label": "Reducir: promedio", "value": "mean"},
                                                   {"label": "Reducir: suma", "value": "sum"},
                                                   {"label": "Reducir: último período", "value": "last"},
                                                   {"label": "Aumentar", "value": "upsample"}],
                                          placeholder="Seleccionar método", searchable=False),
                            className="dash-bootstrap"),
                        dbc.FormText("Define la operación para agrupar o desagrupar períodos",
                                     color="secondary")
                        ])]))], color="primary", outline=True), md=6)
        ], form=True)

    order = dbc.FormGroup([
        dbc.Label(html.H6("Definir orden de transformaciones"), html_for=f"order-{i}"),
        apply_qs(params)(dcc.Dropdown)(id=f"order-{i}", disabled=True,
                                           placeholder="Seleccionar orden de transformaciones",
                                           multi=True),
        dbc.FormText("Las transformaciones se aplican empezando por la izquierda.", color="secondary")])

    return html.Div([table_indicator, html.Br(), first_form, second_form, html.Br(),
                     order, data_storage(i=i), tooltip_builder(i=i)])


def tooltip_builder(i: int):
    return html.Div([
        dbc.Tooltip("Convertir a dólares usando el tipo de cambio interbancario promedio mensual. "
                    "Requiere que el indicador original esté expresado en pesos uruguayos.",
            target=f"usd-header-{i}",
            placement="bottom",
            delay={"show": 250}),
        dbc.Tooltip("Convertir a precios constantes usando el IPC. "
                    "Requiere que el indicador original esté expresado en pesos uruguayos corrientes.",
            target=f"real-header-{i}",
            placement="bottom",
            delay={"show": 250}),
        dbc.Tooltip("Si se selecciona la fecha de inicio, el indicador queda expresado en precios reales de ese período. "
                    "Si se seleccionan ambas fechas, el indicador queda expresado en precios reales promedio del rango. "
                    "Si no se seleccionan fechas, el indicador queda expresado en términos reales sin una unidad.",
            target=f"real-dates-group-{i}",
            placement="bottom",
            delay={"show": 250}),
        dbc.Tooltip("Convertir a ratio del PBI nominal, mensualizando el PBI si es necesario. "
                    "Requiere que el indicador original esté expresado en pesos uruguayos o dólares.",
            target=f"gdp-header-{i}",
            placement="bottom",
            delay={"show": 250}),
        dbc.Tooltip("Modificar la frecuencia de acuerdo a distintos métodos de agregación / desagregación.",
            target=f"resample-header-{i}",
            placement="bottom",
            delay={"show": 250}),
        ])


def form_tabs(params):
    return dbc.Tabs([
        dbc.Tab(
            dbc.Card(
                dbc.CardBody(
                    form_builder(i, params))), label=f"Grupo {i}",
            activeLabelClassName="btn btn-primary") for i in range(1, 4)
        ])


def data_storage(i: int):
    return html.Div([dcc.Store(id=f"data-{i}"),
                     dcc.Store(id=f"metadata-{i}"),
                     dcc.Store(id=f"data-transformed-{i}"),
                     dcc.Store(id=f"metadata-transformed-{i}")])