import datetime as dt
from typing import Sequence

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
from econuy.core import Pipeline
from econuy.session import Session
from econuy import transform
from econuy.utils import sqlutil
from flask import current_app

from econuy_web.dash_apps.querystrings import encode_state, parse_state
from econuy_web.dash_apps.monitor.components import build_layout


def register_callbacks(app):

    from econuy_web import db

    @app.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")],
    )
    def toggle_navbar_collapse(n, is_open):
        if n:
            return not is_open
        return is_open

    id_values = [("dates", "start_date"), ("dates", "end_date")]
    zipped_id_values = list(zip(*id_values))

    @app.callback(
        Output("url", "search"), [Input(id, param) for (id, param) in id_values]
    )
    def update_url_state(*values):
        """
        When any of the (id, param) values changes, this callback gets triggered.

        Passes the list of component id's, the list of component parameters
        (zipped together in component_ids_zipped), and the value to encode_state()
        and return a properly formed querystring.
        """
        return encode_state(zipped_id_values, values)

    @app.callback(Output("page-layout", "children"), [Input("url", "href")])
    def page_load(href):
        """
        Upon page load, take the url, parse the querystring, and use the
        resulting state dictionary to build up the layout.
        """
        if not href:
            return []
        state = parse_state(href)
        return build_layout(state)

    @app.callback(
        Output("chart-demand", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_demand(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("natacc_gas_con_nsa_long")
        # p.chg_diff(period="inter")
        demand = p.dataset
        demand.columns = demand.columns.get_level_values(0)
        demand = (
            demand.div(demand["Producto bruto interno"], axis=0)
            .shift(4)
            .mul(demand.pct_change(4), axis=0)
            * 100
        )
        demand["Importaciones de bienes y servicios"] = (
            demand["Importaciones de bienes y servicios"] * -1
        )
        demand_plot = build_chart(
            demand,
            y=[
                "Gasto de consumo: hogares",
                "Gasto de consumo: gobierno y ISFLH",
                "Formación bruta de capital",
                "Exportaciones de bienes y servicios",
                "Importaciones de bienes y servicios",
            ],
            title="Cuentas nacionales, demanda",
            subtitle="Contribución al crecimiento interanual",
            kind="bar",
            start=start,
            end=end,
            extra_trace="Producto bruto interno",
        )
        return demand_plot

    @app.callback(
        Output("chart-supply", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_supply(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("natacc_ind_con_nsa_long")
        # p.chg_diff(period="inter")
        supply = p.dataset
        supply.columns = supply.columns.get_level_values(0)
        supply = (
            supply.div(supply["Producto bruto interno"], axis=0)
            .shift(4)
            .mul(supply.pct_change(4), axis=0)
            * 100
        )
        supply_plot = build_chart(
            supply,
            y=supply.columns[:-1],
            title="Cuentas nacionales, oferta",
            subtitle="Contribución al crecimiento interanual",
            kind="bar",
            start=start,
            end=end,
            extra_trace="Producto bruto interno",
            height=470,
        )
        return supply_plot

    @app.callback(
        Output("chart-gdp", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_gdp(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("gdp_con_idx_sa_long")
        p.chg_diff(period="last")
        gdp = p.dataset
        gdp.columns = gdp.columns.get_level_values(0)
        gdp_plot = build_chart(
            gdp,
            title="PBI real",
            subtitle="Desestacionalizado, variación trimestral",
            kind="bar",
            start=start,
            end=end,
        )
        return gdp_plot

    @app.callback(
        Output("chart-industrial", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_industrial(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("core_industrial")
        p.chg_diff(period="inter")
        industrial = p.dataset
        industrial.columns = industrial.columns.get_level_values(0)
        industrial_plot = build_chart(
            industrial,
            title="Producción industrial",
            subtitle="Variación interanual",
            kind="line",
            start=start,
            end=end,
        )
        return industrial_plot

    @app.callback(
        Output("chart-inflation", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_cpi(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("cpi")
        p.chg_diff(period="inter")
        cpi = p.dataset
        cpi.columns = cpi.columns.get_level_values(0)
        cpi_plot = build_chart(
            cpi,
            title="IPC",
            subtitle="Variación interanual",
            kind="line",
            start=start,
            end=end,
        )
        return cpi_plot

    @app.callback(
        Output("chart-inflation-measures", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_cpi_measures(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("cpi_measures")
        p.chg_diff(period="inter")
        cpi_measures = p.dataset
        cpi_measures.columns = cpi_measures.columns.get_level_values(0)
        cpi_measures_plot = build_chart(
            cpi_measures,
            title="IPC transable, no transable y subyacente",
            subtitle="Variación interanual",
            kind="line",
            y=cpi_measures.columns[:-2],
            start=start,
            end=end,
            height=460,
        )
        return cpi_measures_plot

    @app.callback(
        Output("chart-nxr", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_nxr(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("nxr_daily")
        nxr_daily = p.dataset
        nxr_daily.columns = nxr_daily.columns.get_level_values(0)
        nxr_plot = build_chart(
            nxr_daily,
            title="Tipo de cambio",
            subtitle="Cable",
            kind="area",
            start=start,
            end=end,
        )
        return nxr_plot

    @app.callback(
        [
            Output("chart-primary-global", "figure"),
            Output("chart-balance-sectors", "figure"),
        ],
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_fiscal_balance(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("balance_summary")
        p.convert(flavor="gdp")
        balance = p.dataset
        balance.columns = balance.columns.get_level_values(0)
        balance_plot = build_chart(
            balance,
            title="Resultado fiscal del sector público consolidado",
            subtitle="% del PBI",
            kind="line",
            start=start,
            end=end,
            y=[
                "Resultado: Primario SPC ex FSS",
                "Resultado: Primario SPC",
                "Resultado: Global SPC ex FSS",
                "Resultado: Global SPC",
            ],
        )
        balance_sectors_plot = build_chart(
            balance,
            title="Resultado global por sector",
            subtitle="% del PBI",
            kind="bar",
            start=start,
            end=end,
            y=[
                "Resultado: Global GC-BPS ex FSS",
                "Resultado: Global EEPP",
                "Resultado: Global intendencias",
                "Resultado: Global BSE",
                "Resultado: Global BCU",
            ],
        )
        return balance_plot, balance_sectors_plot

    @app.callback(
        Output("chart-revenue", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_taxes(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("tax_revenue")
        p.convert(flavor="real")
        p.chg_diff(period="inter")
        tax = p.dataset
        tax[
            [
                "IRAE - Rentas de Actividades Económicas",
                "IRPF Cat II - Rentas de las Personas Físicas",
            ]
        ] = tax[
            [
                "IRAE - Rentas de Actividades Económicas",
                "IRPF Cat II - Rentas de las Personas Físicas",
            ]
        ].mask(
            tax.index.to_series() < "2009-01-01"
        )
        tax.columns = tax.columns.get_level_values(0)
        tax_plot = build_chart(
            tax,
            title="Recaudación impositiva",
            subtitle="Variación interanual",
            kind="line",
            start=start,
            end=end,
            y=[
                "IRAE - Rentas de Actividades Económicas",
                "IRPF Cat II - Rentas de las Personas Físicas",
                "IVA - Valor Agregado",
                "Recaudación Total de la DGI",
            ],
        )
        return tax_plot

    @app.callback(
        Output("chart-debt", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_debt(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("net_public_debt")
        p.convert(flavor="gdp")
        debt = p.dataset
        debt.columns = debt.columns.get_level_values(0)
        debt_plot = build_chart(
            debt,
            title="Deuda neta del sector público global",
            subtitle="% del PBI",
            kind="area",
            start=start,
            end=end,
        )
        return debt_plot

    @app.callback(
        [
            Output("chart-activity-employment", "figure"),
            Output("chart-unemployment", "figure"),
        ],
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_labor_rates(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("labor_rates_people")
        nsa = p.dataset
        nsa.columns = nsa.columns.get_level_values(0)
        trends = sqlutil.read(con=db.engine, table_name="labor_rates_people_seas")
        trends.columns = trends.columns.get_level_values(0) + [" (tendencia-ciclo)"]
        data = pd.concat([nsa, trends], axis=1)
        activity_employment_plot = build_chart(
            data,
            title="Actividad y empleo",
            subtitle="Tasa",
            kind="line",
            start=start,
            end=end,
            y=[
                "Tasa de actividad",
                "Tasa de actividad (tendencia-ciclo)",
                "Tasa de empleo",
                "Tasa de empleo (tendencia-ciclo)",
            ],
            height=460,
        )
        unemployment_plot = build_chart(
            data,
            title="Desempleo",
            subtitle="Tasa",
            kind="line",
            start=start,
            end=end,
            y=["Tasa de desempleo", "Tasa de desempleo (tendencia-ciclo)"],
        )

        return activity_employment_plot, unemployment_plot

    @app.callback(
        Output("chart-real-wages", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_wages(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("real_wages")
        p.chg_diff(period="inter")
        wages = p.dataset
        wages.columns = wages.columns.get_level_values(0)
        wages_plot = build_chart(
            wages,
            title="Salario real",
            subtitle="Variación interanual",
            kind="line",
            start=start,
            end=end,
        )
        return wages_plot

    @app.callback(
        Output("chart-exp-imp", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_expimp(start, end):
        s = Session(location=db.engine, download=False)
        s.get(["trade_x_prod_val", "trade_m_sect_val"])
        s.convert(flavor="gdp")
        s.concat(concat_name="expimp")
        data = s.datasets["concat_expimp"]
        data.columns = data.columns.get_level_values(0)
        expimp_plot = build_chart(
            data,
            title="Exportaciones e importaciones",
            subtitle="% del PBI",
            kind="line",
            start=start,
            end=end,
            y=["Total exportaciones", "Total importaciones: CIF "],
        )
        return expimp_plot

    @app.callback(
        Output("chart-tot", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_tot(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("terms_of_trade")
        p.chg_diff(period="inter")
        tot = p.dataset
        tot.columns = tot.columns.get_level_values(0)
        tot_plot = build_chart(
            tot,
            title="Términos de intercambio",
            subtitle="Variación interanual",
            kind="area",
            start=start,
            end=end,
        )
        return tot_plot

    @app.callback(
        Output("chart-rxr", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_rxr(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("rxr_custom")
        p.rebase(start_date=p.dataset.index.min(), end_date=p.dataset.index.max())
        rxr = p.dataset
        rxr.columns = rxr.columns.get_level_values(0)
        rxr_plot = build_chart(
            rxr,
            title=f"Tipo de cambio real",
            subtitle=f"1980-{dt.date.today().year}=100",
            kind="line",
            start=start,
            end=end,
        )
        return rxr_plot

    @app.callback(
        Output("chart-commodity-index", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_commodity(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("commodity_index")
        p.chg_diff(period="inter")
        commodity = p.dataset
        commodity.columns = commodity.columns.get_level_values(0)
        commodity_plot = build_chart(
            commodity,
            title="Índice de precios de commodities",
            subtitle="Variación interanual",
            kind="area",
            start=start,
            end=end,
        )
        return commodity_plot

    @app.callback(
        Output("chart-ubi", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_ubi(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("sovereign_risk")
        ubi = p.dataset
        ubi.columns = ubi.columns.get_level_values(0)
        ubi_plot = build_chart(
            ubi,
            title="Uruguay Bond Index",
            subtitle="Spread con respecto Treasury 10Y",
            kind="area",
            start=start,
            end=end,
        )
        return ubi_plot

    @app.callback(
        Output("chart-bonds", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_bonds(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("bonds")
        bonds = p.dataset
        bonds.columns = bonds.columns.get_level_values(0)
        bonds_plot = build_chart(
            bonds,
            title="Rendimiento de bonos soberanos",
            subtitle="Puntos básicos",
            kind="line",
            start=start,
            end=end,
        )
        return bonds_plot

    @app.callback(
        Output("chart-regional-gdp", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_regional_gdp(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("regional_monthly_gdp")
        p.chg_diff(period="inter")
        gdp = p.dataset
        gdp.columns = gdp.columns.get_level_values(0)
        gdp_plot = build_chart(
            gdp,
            title="PBI mensual",
            subtitle="Variación interanual",
            kind="line",
            start=start,
            end=end,
        )
        return gdp_plot

    @app.callback(
        Output("chart-regional-nxr", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_regional_nxr(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("regional_nxr")
        nxr = p.dataset.pct_change(30) * 100
        nxr.columns = nxr.columns.get_level_values(0)
        rxr_plot = build_chart(
            nxr,
            title="Tipo de cambio nominal",
            subtitle="Variación 30 días",
            kind="line",
            start=start,
            end=end,
        )
        return rxr_plot

    @app.callback(
        Output("chart-global-gdp", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_global_gdp(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("global_gdp")
        p.chg_diff(period="inter")
        gdp = p.dataset[["Estados Unidos", "Unión Europea", "China"]]
        gdp.columns = gdp.columns.get_level_values(0)
        gdp_plot = build_chart(
            gdp,
            title="PBI real",
            subtitle="Variación interanual",
            kind="line",
            start=start,
            end=end,
        )
        return gdp_plot

    @app.callback(
        Output("chart-global-nxr", "figure"),
        [Input("dates", "start_date"), Input("dates", "end_date")],
    )
    def build_global_nxr(start, end):
        p = Pipeline(location=db.engine, download=False)
        p.get("global_nxr")
        nxr = p.dataset[["Índice Dólar", "Euro", "Renminbi"]].pct_change(30) * 100
        nxr.columns = nxr.columns.get_level_values(0)
        nxr_plot = build_chart(
            nxr,
            title="Tipo de cambio nominal",
            subtitle="Variación 30 días",
            kind="line",
            start=start,
            end=end,
        )
        return nxr_plot


def build_chart(
    data: pd.DataFrame,
    title: str,
    subtitle: str,
    y: Sequence = None,
    kind: str = "line",
    yaxis_label: str = None,
    y_tickformat: str = None,
    start: str = None,
    end: str = None,
    extra_trace: str = None,
    **kwargs,
):
    start = start or "1900-01-01"
    end = end or dt.date.today().strftime("%Y-%m-%d")
    data = data.loc[start:end]
    # if len(data) > 7000:
    full_title = f"{title}<br><span style='font-size:14px'>{subtitle}</span>"
    if y is None:
        y = data.columns
    if kind == "line":
        fig = px.line(
            data,
            y=y,
            color_discrete_sequence=px.colors.qualitative.Bold,
            title=full_title,
            **kwargs,
        )
    elif kind == "bar":
        fig = px.bar(
            data,
            y=y,
            color_discrete_sequence=px.colors.qualitative.Bold,
            title=full_title,
            **kwargs,
        )
    else:
        fig = px.area(
            data,
            y=y,
            color_discrete_sequence=px.colors.qualitative.Bold,
            title=full_title,
            **kwargs,
        )
    if extra_trace is not None:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data[extra_trace],
                mode="lines",
                line=go.scatter.Line(color="black"),
                name=extra_trace,
            )
        )
    fig.update_layout(
        {
            "margin": {"l": 20, "r": 20},
            "legend": {
                "orientation": "h",
                "yanchor": "top",
                "y": -0.1,
                "xanchor": "left",
                "x": 0,
            },
            "legend_orientation": "h",
            "xaxis_title": "",
            "yaxis_title": yaxis_label or "",
            "legend_title": "",
            "title": {"y": 0.9, "yanchor": "top", "font": {"size": 16}},
            "yaxis_tickformat": y_tickformat or "",
        }
    )
    return fig
