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
        [Output("gdp", "figure"),
         Output("prices", "figure"),
         Output("act-emp", "figure"),
         Output("unemp", "figure"),
         Output("deficit", "figure"),
         Output("debt", "figure"),
         Output("trade", "figure"),
         Output("nxr", "figure")],
        [Input("dates", "start_date"),
         Input("dates", "end_date")])
    def build_dashboard(start_date, end_date):
        start_date = start_date or "2010-01-01"
        end_date = end_date or "2100-01-01"

        cpi = sqlutil.read(con=db.engine, table_name="tfm_prices")
        cpi = cpi.iloc[:, 0:4]
        cpi = transform.chg_diff(cpi, operation="chg", period_op="inter")
        cpi.columns = cpi.columns.get_level_values(0).str.replace(
            "Índice de precios al consumo: ", "").str.capitalize()

        gdp = sqlutil.read(con=db.engine,
                           table_name="naccounts_ind_con_idx_sa")
        gdp = gdp.iloc[:, [-1]]
        gdp = transform.chg_diff(gdp, operation="chg", period_op="last")

        labor = sqlutil.read(con=db.engine,
                             table_name="tfm_labor_extended_nsa")
        labor = labor.iloc[:, 0:3]
        labor_decomp = transform.decompose(labor, flavor="trend",
                                           method="loess")
        act_emp = pd.concat([labor.iloc[:, [0]],
                             labor_decomp.iloc[:, [0]]], axis=1)
        act_emp.columns = ["Empleo", "Empleo desestacionalizado"]
        unemp = pd.concat([labor.iloc[:, [2]],
                           labor_decomp.iloc[:, [2]]], axis=1)
        unemp.columns = ["Desempleo", "Desempleo desestacionalizado"]

        deficit = sqlutil.read(con=db.engine,
                               table_name="tfm_fiscal_gps_uyu_fssadj")
        deficit = deficit.iloc[:, [-1]]
        deficit = transform.convert_gdp(deficit, update_loc=db.engine,
                                        only_get=True)

        debt = sqlutil.read(con=db.engine,
                            table_name="tfm_pubdebt")
        debt = transform.convert_gdp(debt, update_loc=db.engine,
                                     only_get=True)

        exports = sqlutil.read(con=db.engine,
                               table_name="tb_x_dest_val")
        imports = sqlutil.read(con=db.engine,
                               table_name="tb_m_orig_val")
        trade = pd.concat([exports.iloc[:, [0]], imports.iloc[:, [0]]], axis=1)
        trade = transform.rolling(trade, periods=12, operation="sum")
        trade.columns = ["Exportaciones", "Importaciones"]

        nxr = sqlutil.read(con=db.engine,
                           table_name="nxr_daily")

        yaxis_titles = ["% crecimiento trimestral", "% variación interanual",
                        "Tasa", "Tasa", "% del PBI", "% del PBI",
                        "Millones de dólares, acumulado 12 meses", "Pesos por dólar"]
        plot_titles = ["Crecimiento económico", "Indicadores de inflación",
                       "Empleo", "Desempleo", "Déficit fiscal",
                       "Deuda pública", "Comercio internacional",
                       "Tipo de cambio interbancario"]
        figures = []
        for df, yaxis, chart_type, title in zip(
                [gdp, cpi, act_emp, unemp, deficit, debt, trade, nxr],
                yaxis_titles,
                [px.bar, px.line, px.line, px.line, px.bar, px.line, px.line,
                 px.line],
                plot_titles):
            df = df.loc[(df.index >= start_date) & (df.index <= end_date)]
            fig = chart_type(data_frame=df, x=df.index,
                             y=df.columns.get_level_values(0),
                             title=title,
                             color_discrete_sequence=px.colors.qualitative.Vivid,
                             template="plotly_white")
            fig.update_layout({"margin": {"l": 0, "r": 15},
                               "legend": {"orientation": "h", "yanchor": "top",
                                          "y": -0.1, "xanchor": "left",
                                          "x": 0},
                               "legend_orientation": "h",
                               "xaxis_title": "",
                               "yaxis_title": yaxis,
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
            figures.append(fig)
        return figures
