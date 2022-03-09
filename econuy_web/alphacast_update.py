import os
import re
from pathlib import Path

from alphacast import Alphacast
from dotenv import load_dotenv
from sqlalchemy import create_engine
from econuy.utils import datasets
from econuy import Session, Pipeline
from econuy import transform

from econuy_web.tasks import get_project_root


load_dotenv(Path(get_project_root(), ".env"))
ALPHACAST_API_KEY = os.environ.get("ALPHACAST_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
AREA_TRANSLATIONS = {
    "Actividad económica": "Activity",
    "Precios": "Prices",
    "Precios y salarios": "Prices",
    "Sector externo": "External sector",
    "Ingresos": "Income",
    "Global": "Global",
    "Mercado laboral": "Labor market",
    "Regional": "Regional",
    "Sector público": "Public sector",
    "Sector financiero": "Financial sector",
}
FREQ_TRANSLATIONS = {
    "Q-DEC": "Quarterly",
    "Q": "Quarterly",
    "A-DEC": "Annual",
    "A": "Annual",
    "M": "Monthly",
    "MS": "Monthly",
    "W": "Weekly",
    "W-SUN": "Weekly",
    "D": "Daily",
    "-": "Daily",
}

eng = create_engine(DATABASE_URL)
p = Pipeline(location=eng, download=False)

alphacast = Alphacast(ALPHACAST_API_KEY)
PUBLIC_REPO_DESCRIPTION = (
    "This is econuy's (https://econ.uy) public repository. It contains "
    "Uruguayan economy datasets as provided by government sources in a "
    "friendly tabular format. Check out the private repo for datasets "
    "with custom transformations and combinations."
)
PRIVATE_REPO_DESCRIPTION = (
    "This is econuy's (https://econ.uy) private repository. It contains "
    "custom Uruguayan economy datasets processed from government data. It "
    "includes indicators like core inflation, custom long-run market labor "
    "data and the commodity price index."
)
TRANSFORMATIONS = {
    "Public sector - Uruguay - Fiscal balance: consolidated public sector (% GDP) - Monthly": {
        "base": "balance_gps",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "Public sector - Uruguay - Fiscal balance: non-financial public sector (% GDP) - Monthly": {
        "base": "balance_nfps",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "Public sector - Uruguay - Fiscal balance: central government-BPS (% GDP) - Monthly": {
        "base": "balance_cg-bps",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "Public sector - Uruguay - Fiscal balance: public enterprises (% GDP) - Monthly": {
        "base": "balance_pe",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "Public sector - Uruguay - Tax revenue by source (real, YoY % chg) - Monthly": {
        "base": "tax_revenue",
        "transformations": [
            lambda x: transform.convert_real(x, pipeline=p),
            lambda x: transform.chg_diff(x, period="inter"),
        ],
    },
    "Public sector - Uruguay - General government debt: by contractual term, residual, currency and residence (% GDP) - Quarterly": {
        "base": "public_debt_gps",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "Public sector - Uruguay - Non-monetary government debt: by contractual term, residual, currency and residence (% GDP) - Quarterly": {
        "base": "public_debt_nfps",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "Public sector - Uruguay - Central bank debt: by contractual term, residual, currency and residence (% GDP) - Quarterly": {
        "base": "public_debt_cb",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "Labor market - Uruguay - Real wages: total, public and private (YoY % chg) - Monthly": {
        "base": "real_wages",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
    "Financial sector - Uruguay - Bank deposits (% GDP) - Monthly": {
        "base": "deposits",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "Financial sector - Uruguay - Bank credits to non-financial sector (% GDP) - Monthly": {
        "base": "credit",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "Prices - Uruguay - Consumer price index - CPI (YoY % chg) - Monthly": {
        "base": "cpi",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
    "Activity - Uruguay - Industrial production: total, ex-refinery and core (YoY % chg) - Monthly": {
        "base": "core_industrial",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
    "Activity - Uruguay - National accounts: supply, constant prices, spliced series (YoY % chg) - Quarterly": {
        "base": "natacc_ind_con_nsa_long",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
    "Activity - Uruguay - National accounts: supply, constant prices, spliced series (YoY % chg) - Quarterly": {
        "base": "natacc_gas_con_nsa_long",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
    "Activity - Uruguay - GDP: real index, seasonally adjusted, spliced series (QoQ % chg) - Quarterly": {
        "base": "gdp_con_idx_sa_long",
        "transformations": [lambda x: transform.chg_diff(x, period="last")],
    },
    "Activity - Uruguay - GDP: constant prices, spliced series (wp BCU 12-15) (YoY % chg) - Quarterly": {
        "base": "gdp_con_nsa_long",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
    "Prices - Uruguay - CPI: tradable, non-tradable, core and residual (YoY % chg) - Monthly": {
        "base": "cpi_measures",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
    "Prices - Uruguay - CPI: tradable, non-tradable, core and residual (MoM % chg, seasonally adjusted) - Monthly": {
        "base": "cpi_measures",
        "transformations": [
            lambda x: transform.chg_diff(x, period="last"),
            lambda x: transform.decompose(x, component="seas", force_x13=True),
        ],
    },
    "Public sector - Uruguay - Fiscal balance: all aggregations, inc. FSS adjustment (% GDP) - Monthly": {
        "base": "balance_summary",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "Public sector - Uruguay - Net public debt excluding bank deposits (% GDP) - Quarterly": {
        "base": "net_public_debt",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "Labor market - Uruguay - Labor force participation, employment and unemployment: extended series of rates and people (seasonally adjusted) - Monthly": {
        "base": "labor_rates_people",
        "transformations": [
            lambda x: transform.decompose(x, component="seas", force_x13=True)
        ],
    },
    "Labor market - Uruguay - Labor force participation, employment and unemployment: extended series of rates and people (trend-cycle) - Monthly": {
        "base": "labor_rates_people",
        "transformations": [
            lambda x: transform.decompose(x, component="trend", force_x13=True)
        ],
    },
    "External sector - Uruguay - Trade balance by country (% GDP) - Monthly": {
        "base": "trade_balance",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "External sector - Uruguay - Terms of trade (YoY % chg) - Monthly": {
        "base": "terms_of_trade",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
    "External sector - Uruguay - Econuy commodity price index (YoY % chg) - Monthly": {
        "base": "commodity_index",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
    "External sector - Uruguay - Real exchange rates, econuy calculations (YoY % chg) - Monthly": {
        "base": "rxr_custom",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
    "External sector - Uruguay - Balance of payments (% GDP) - Quarterly": {
        "base": "bop",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "External sector - Uruguay - Balance of payments summary and capital flows (% GDP) - Quarterly": {
        "base": "bop_summary",
        "transformations": [lambda x: transform.convert_gdp(x, pipeline=p)],
    },
    "Prices - Uruguay - Produce price index - PPI (YoY % chg) - Monthly": {
        "base": "ppi",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
    "Prices - Uruguay - Producer price index - PPI (MoM % chg, seasonally adjusted) - Monthly": {
        "base": "ppi",
        "transformations": [
            lambda x: transform.chg_diff(x, period="last"),
            lambda x: transform.decompose(x, component="seas", force_x13=True),
        ],
    },
    "Prices - Uruguay - CPI by division - CPI (YoY % chg) - Monthly": {
        "base": "cpi_divisions",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
    "Prices - Uruguay - CPI by division - CPI (MoM % chg, seasonally adjusted) - Monthly": {
        "base": "cpi_divisions",
        "transformations": [
            lambda x: transform.chg_diff(x, period="last"),
            lambda x: transform.decompose(x, component="seas", force_x13=True),
        ],
    },
    "Prices - Uruguay - Utilities' price index (YoY % chg) - Monthly": {
        "base": "utilities",
        "transformations": [lambda x: transform.chg_diff(x, period="inter")],
    },
}


def build_dataset_name(dataset, name_es):
    area_es = dataset.columns[0][1]
    area_en = AREA_TRANSLATIONS[area_es]
    try:
        name_en = datasets.original()[name_es]["description_en"]
    except KeyError:
        name_en = datasets.custom()[name_es]["description_en"]
    name_en = re.sub(r" \(([^)]+)\)$", "", name_en)
    freq = dataset.columns[0][2]
    freq_trns = FREQ_TRANSLATIONS[freq]
    return f"{area_en} - Uruguay - {name_en} - {freq_trns}"


def upload_public_datasets():
    repo_details = alphacast.repository.create(
        "Uruguay Macro (econuy public repo)",
        repo_description=PUBLIC_REPO_DESCRIPTION,
        slug="public-repo",
        privacy="Public",
        returnIdIfExists=True,
    )
    repo_id = repo_details["id"]

    s = Session(location=eng, download=False)
    s.get_bulk("original")
    for name, dataset in s.datasets.items():
        upload_dataset(dataset, name, repo_id)

    return


def upload_private_datasets():
    repo_details = alphacast.repository.create(
        "Uruguay Macro (econuy private repo)",
        repo_description=PRIVATE_REPO_DESCRIPTION,
        slug="private-repo",
        privacy="Private",
        returnIdIfExists=True,
    )
    repo_id = repo_details["id"]

    s = Session(location=eng, download=False)
    custom_only_uruguay = [
        x
        for x in datasets.custom().keys()
        if not any([y in x for y in ["global", "regional", "lin_gdp"]])
    ]
    s.get(custom_only_uruguay)
    for name, dataset in s.datasets.items():
        upload_dataset(dataset, name, repo_id)

    return


def upload_transformed_datasets():
    repo_details = alphacast.repository.create(
        "Uruguay Macro (econuy private repo)",
        repo_description=PRIVATE_REPO_DESCRIPTION,
        slug="private-repo",
        privacy="Private",
        returnIdIfExists=True,
    )
    repo_id = repo_details["id"]

    for name, dataset_dict in TRANSFORMATIONS.items():
        p.get(dataset_dict["base"])
        data = p.dataset
        for transformation in dataset_dict["transformations"]:
            data = transformation(data)
        data.columns = data.columns.get_level_values(0)
        upload_dataset(data, "", repo_id, full_name=name)

    return


def upload_dataset(dataset, name, repo_id, full_name=None):
    aux = dataset.copy()
    if full_name is None:
        dataset_name = build_dataset_name(aux, name)
    else:
        dataset_name = full_name
    aux.columns = aux.columns.get_level_values(0)
    aux.insert(0, column="country", value="Uruguay")
    aux.reset_index(inplace=True)
    aux.rename(columns={"index": "Date"}, inplace=True)
    try:
        dataset_details = alphacast.datasets.create(dataset_name, repo_id)
        dataset_id = dataset_details["id"]
    except KeyError:
        dataset_id = alphacast.datasets.read_by_name(dataset_name)["id"]
    alphacast.datasets.dataset(dataset_id).initialize_columns(
        dateColumnName="Date", entitiesColumnNames=["country"], dateFormat="%Y-%m-%d"
    )
    alphacast.datasets.dataset(dataset_id).upload_data_from_df(
        aux, deleteMissingFromDB=True, onConflictUpdateDB=True, uploadIndex=False
    )
    return


if __name__ == "__main__":
    upload_public_datasets()
    upload_private_datasets()
    upload_transformed_datasets()
