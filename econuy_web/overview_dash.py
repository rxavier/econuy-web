import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
from dash import Dash
from dash.dependencies import Input, Output
from flask import url_for

from econuy import transform
from econuy.utils import sqlutil

external_stylesheets = [dbc.themes.FLATLY]

url_base = "/dash/overview/"


def add_dash(server):
    app = Dash(server=server, url_base_pathname=url_base,
               external_stylesheets=external_stylesheets)
    app.layout = html.Div([
        html.H1("Economía uruguaya de un vistazo"),
        html.Br(),
        html.Div(dcc.DatePickerRange(id="dates",
                                     start_date_placeholder_text="Fecha inicial",
                                     end_date_placeholder_text="Fecha final",
                                     display_format="DD-MM-YYYY"),
                 style={"margin": "0 auto", "width": "300px"}),
        html.Br(),
        html.Div([
            html.Div(className="loader-wrapper",
                     children=dcc.Loading(dcc.Graph(id="gdp", figure=[],
                                                    config={
                                                        'displayModeBar': False
                                                    })),
                     style={"display": "inline-block", "width": "46%"}),
            html.Div(className="loader-wrapper",
                     children=dcc.Loading(dcc.Graph(id="prices", figure=[],
                                                    config={
                                                        'displayModeBar': False
                                                    })),
                     style={"display": "inline-block", "width": "46%"})]),
        html.Div([
            html.Div(className="loader-wrapper",
                     children=dcc.Loading(dcc.Graph(id="emp", figure=[],
                                                    config={
                                                        'displayModeBar': False
                                                    })),
                     style={"display": "inline-block", "width": "46%"}),
            html.Div(className="loader-wrapper",
                     children=dcc.Loading(dcc.Graph(id="unemp", figure=[],
                                                    config={
                                                        'displayModeBar': False
                                                    })),
                     style={"display": "inline-block", "width": "46%"})]),
        html.Div([
            html.Div(className="loader-wrapper",
                     children=dcc.Loading(dcc.Graph(id="deficit", figure=[],
                                                    config={
                                                        'displayModeBar': False
                                                    })),
                     style={"display": "inline-block", "width": "46%"}),
            html.Div(className="loader-wrapper",
                     children=dcc.Loading(dcc.Graph(id="debt", figure=[],
                                                    config={
                                                        'displayModeBar': False
                                                    })),
                     style={"display": "inline-block", "width": "46%"})]),
        html.Div([
            html.Div(className="loader-wrapper",
                     children=dcc.Loading(dcc.Graph(id="trade", figure=[],
                                                    config={
                                                        'displayModeBar': False
                                                    })),
                     style={"display": "inline-block", "width": "46%"}),
            html.Div(className="loader-wrapper",
                     children=dcc.Loading(dcc.Graph(id="nxr", figure=[],
                                                    config={
                                                        'displayModeBar': False
                                                    })),
                     style={"display": "inline-block", "width": "46%"})])
    ])

    register_callbacks(app)

    return app.server


def register_callbacks(app):
    from econuy_web import db

    @app.callback(
        Output("gdp", "figure"),
        [Input("dates", "start_date"),
         Input("dates", "end_date")])
    def activity(start_date, end_date):
        start_date = start_date or "2010-01-01"
        end_date = end_date or "2100-01-01"

        gdp = sqlutil.read(con=db.engine,
                           table_name="naccounts_ind_con_idx_sa")
        gdp = gdp.iloc[:, [-1]]
        gdp = transform.chg_diff(gdp, operation="chg", period="last")
        gdp = gdp.loc[(gdp.index >= start_date) & (gdp.index <= end_date)]

        return generate_plot(df=gdp, chart_type=px.bar, title="Crecimiento",
                             y_axis_title="% crecimiento trimestral")

    @app.callback(
        Output("prices", "figure"),
        [Input("dates", "start_date"),
         Input("dates", "end_date")])
    def inflation(start_date, end_date):
        start_date = start_date or "2010-01-01"
        end_date = end_date or "2100-01-01"

        cpi = sqlutil.read(con=db.engine, table_name="cpi_measures")
        cpi = cpi.iloc[:, 0:4]
        cpi = transform.chg_diff(cpi, operation="chg", period="inter")
        cpi.columns = cpi.columns.get_level_values(0).str.replace(
            "Índice de precios al consumo: ", "").str.capitalize()
        cpi = cpi.loc[(cpi.index >= start_date) & (cpi.index <= end_date)]

        return generate_plot(df=cpi, chart_type=px.line, title="Inflación",
                             y_axis_title="% variación interanual")

    @app.callback(
        Output("deficit", "figure"),
        [Input("dates", "start_date"),
         Input("dates", "end_date")])
    def fiscal(start_date, end_date):
        start_date = start_date or "2010-01-01"
        end_date = end_date or "2100-01-01"

        deficit = sqlutil.read(con=db.engine,
                               table_name="balance_fss_gps_fssadj")
        deficit = deficit.iloc[:, [-1]]
        deficit = transform.convert_gdp(deficit, update_loc=db.engine,
                                        only_get=True)
        deficit = deficit.loc[(deficit.index >= start_date) &
                              (deficit.index <= end_date)]

        return generate_plot(df=deficit, chart_type=px.bar,
                             title="Déficit fiscal", y_axis_title="% del PBI")

    @app.callback(
        Output("debt", "figure"),
        [Input("dates", "start_date"),
         Input("dates", "end_date")])
    def debt(start_date, end_date):
        start_date = start_date or "2010-01-01"
        end_date = end_date or "2100-01-01"

        net_debt = sqlutil.read(con=db.engine,
                            table_name="net_public_debt")
        net_debt = transform.convert_gdp(net_debt, update_loc=db.engine,
                                         only_get=True)
        net_debt = net_debt.loc[(net_debt.index >= start_date) &
                                (net_debt.index <= end_date)]

        return generate_plot(df=net_debt, chart_type=px.line,
                             title="Deuda pública", y_axis_title="% del PBI")

    @app.callback(
        Output("trade", "figure"),
        [Input("dates", "start_date"),
         Input("dates", "end_date")])
    def trade(start_date, end_date):
        start_date = start_date or "2010-01-01"
        end_date = end_date or "2100-01-01"

        exports = sqlutil.read(con=db.engine,
                               table_name="trade_x_dest_val")
        imports = sqlutil.read(con=db.engine,
                               table_name="trade_m_orig_val")
        x_m = pd.concat([exports.iloc[:, [0]], imports.iloc[:, [0]]], axis=1)
        x_m = transform.rolling(x_m, window=12, operation="sum")
        x_m.columns = ["Exportaciones", "Importaciones"]
        x_m = x_m.loc[(x_m.index >= start_date) & (x_m.index <= end_date)]

        return generate_plot(df=x_m, chart_type=px.line, title="Comercio",
                             y_axis_title="Mill. de dólares, acum. 12m")

    @app.callback(
        Output("nxr", "figure"),
        [Input("dates", "start_date"),
         Input("dates", "end_date")])
    def nxr(start_date, end_date):
        start_date = start_date or "2010-01-01"
        end_date = end_date or "2100-01-01"

        interbank = sqlutil.read(con=db.engine,
                           table_name="nxr_daily")
        interbank = interbank.loc[(interbank.index >= start_date) &
                                  (interbank.index <= end_date)]

        return generate_plot(df=interbank, chart_type=px.line,
                             title="Tipo de cambio", y_axis_title="Pesos por dólar")

    @app.callback(
        [Output("unemp", "figure"),
         Output("emp", "figure")],
        [Input("dates", "start_date"),
         Input("dates", "end_date")])
    def emp_unemp(start_date, end_date):
        start_date = start_date or "2010-01-01"
        end_date = end_date or "2100-01-01"

        labor = sqlutil.read(con=db.engine,
                             table_name="rates_people")
        labor = labor.iloc[:, 0:3]
        labor_decomp = transform.decompose(labor, component="trend",
                                           method="x13")
        emp = pd.concat([labor.iloc[:, [0]],
                         labor_decomp.iloc[:, [0]]], axis=1)
        emp.columns = ["Empleo", "Empleo tendencia-ciclo"]
        unemp = pd.concat([labor.iloc[:, [2]],
                           labor_decomp.iloc[:, [2]]], axis=1)
        unemp.columns = ["Desempleo", "Desempleo tendencia-ciclo"]
        emp = emp.loc[(emp.index >= start_date) & (emp.index <= end_date)]
        unemp = unemp.loc[(unemp.index >= start_date) &
                          (unemp.index <= end_date)]

        return (generate_plot(df=unemp, chart_type=px.line, title="Desempleo",
                              y_axis_title="Tasa"),
                generate_plot(df=emp, chart_type=px.line, title="Empleo",
                              y_axis_title="Tasa"))


def generate_plot(df, chart_type, title, y_axis_title):
    df.reset_index(inplace=True)
    df.columns = df.columns.get_level_values(0)
    fig = chart_type(data_frame=df, x="index",
                     y=df.columns,
                     title=title,
                     color_discrete_sequence=px.colors.qualitative.Vivid,
                     template="plotly_white")
    fig.update_layout({"margin": {"l": 0, "r": 15},
                       "legend": {"orientation": "h", "yanchor": "top",
                                  "y": -0.1, "xanchor": "left",
                                  "x": 0},
                       "legend_orientation": "h",
                       "xaxis_title": "",
                       "yaxis_title": y_axis_title,
                       "legend_title": "",
                       "title": {"y": 0.9,
                                 "yanchor": "top",
                                 "font": {"size": 20}}})
    fig.add_layout_image(dict(source=url_for("static",
                                             filename="logo.png"),
                              sizex=0.1, sizey=0.1, xanchor="right",
                              yanchor="bottom", xref="paper",
                              yref="paper",
                              x=1, y=1.01))
    return fig
