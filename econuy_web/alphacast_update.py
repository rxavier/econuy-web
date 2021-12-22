import os
import re
from pathlib import Path

from alphacast import Alphacast
from dotenv import load_dotenv
from sqlalchemy import create_engine
from econuy.utils import datasets
from econuy import Session

from econuy_web.tasks import get_project_root


load_dotenv(Path(get_project_root(), ".env"))
ALPHACAST_API_KEY = os.environ.get("ALPHACAST_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
AREA_TRANSLATIONS = {"Actividad económica": "Activity",
                     "Precios": "Prices",
                     "Precios y salarios": "Prices",
                     "Sector externo": "External sector",
                     "Ingresos": "Income",
                     "Global": "Global",
                     "Mercado laboral": "Labor market",
                     "Regional": "Regional",
                     "Sector público": "Public sector",
                     "Sector financiero": "Financial sector"}
FREQ_TRANSLATIONS = {"Q-DEC": "Quarterly",
                     "Q": "Quarterly",
                     "A-DEC": "Annual",
                     "A": "Annual",
                     "M": "Monthly",
                     "MS": "Monthly",
                     "W": "Weekly",
                     "W-SUN": "Weekly",
                     "D": "Daily",
                     "-": "Daily"}

eng = create_engine(DATABASE_URL)

alphacast = Alphacast(ALPHACAST_API_KEY)
PUBLIC_REPO_DESCRIPTION = ("This is econuy's (https://econ.uy) public repository. It contains "
                           "Uruguayan economy datasets as provided by government sources in a "
                           "friendly tabular format. Check out the private repo for datasets "
                           "with custom transformations and combinations.")
PRIVATE_REPO_DESCRIPTION = ("This is econuy's (https://econ.uy) private repository. It contains "
                           "custom Uruguayan economy datasets processed from government data. It "
                           "includes indicators like core inflation, custom long-run market labor "
                           "data and the commodity price index.")


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
    repo_details = alphacast.repository.create("Uruguay Macro (econuy public repo)",
                                               repo_description=PUBLIC_REPO_DESCRIPTION,
                                               slug="public-repo", privacy="Public",
                                               returnIdIfExists=True)
    repo_id = repo_details["id"]

    s = Session(location=eng, download=False)
    s.get_bulk("original")
    for name, dataset in s.datasets.items():
        aux = dataset.copy()
        dataset_name = build_dataset_name(aux, name)
        aux.columns = aux.columns.get_level_values(0)
        aux.insert(0, column="country", value="Uruguay")
        aux.reset_index(inplace=True)
        aux.rename(columns={"index": "Date"}, inplace=True)
        try:
            dataset_details = alphacast.datasets.create(dataset_name, repo_id)
            dataset_id = dataset_details["id"]
        except KeyError:
            dataset_id = alphacast.datasets.read_by_name(dataset_name)["id"]
        alphacast.datasets.dataset(dataset_id).initialize_columns(dateColumnName="Date",
                                                                             entitiesColumnNames=["country"],
                                                                             dateFormat="%Y-%m-%d")
        alphacast.datasets.dataset(dataset_id).upload_data_from_df(aux,
                                                                   deleteMissingFromDB=False,
                                                                   onConflictUpdateDB=True,
                                                                   uploadIndex=False)

    return


def upload_private_datasets():
    repo_details = alphacast.repository.create("Uruguay Macro (econuy private repo)",
                                               repo_description=PRIVATE_REPO_DESCRIPTION,
                                               slug="private-repo", privacy="Private",
                                               returnIdIfExists=True)
    repo_id = repo_details["id"]

    s = Session(location=eng, download=False)
    custom_only_uruguay = [x for x in datasets.custom().keys()
                           if not any([y in x for y in ["global", "regional", "lin_gdp"]])]
    s.get(custom_only_uruguay)
    for name, dataset in s.datasets.items():
        aux = dataset.copy()
        dataset_name = build_dataset_name(aux, name)
        aux.columns = aux.columns.get_level_values(0)
        aux.insert(0, column="country", value="Uruguay")
        aux.reset_index(inplace=True)
        aux.rename(columns={"index": "Date"}, inplace=True)
        try:
            dataset_details = alphacast.datasets.create(dataset_name, repo_id)
            dataset_id = dataset_details["id"]
        except KeyError:
            dataset_id = alphacast.datasets.read_by_name(dataset_name)["id"]
        alphacast.datasets.dataset(dataset_id).initialize_columns(dateColumnName="Date",
                                                                             entitiesColumnNames=["country"],
                                                                             dateFormat="%Y-%m-%d")
        alphacast.datasets.dataset(dataset_id).upload_data_from_df(aux,
                                                                   deleteMissingFromDB=False,
                                                                   onConflictUpdateDB=True,
                                                                   uploadIndex=False)

    return


def upload_test_datasets():
    repo_details = alphacast.repository.create("test",
                                               repo_description="this is a test",
                                               slug="test-repo", privacy="Private",
                                               returnIdIfExists=True)
    repo_id = repo_details["id"]

    s = Session(location=eng, download=False)
    s.get(["cpi", "cpi_measures"])
    for name, dataset in s.datasets.items():
        aux = dataset.copy()
        dataset_name = build_dataset_name(aux, name)
        aux.columns = aux.columns.get_level_values(0)
        aux.insert(0, column="country", value="Uruguay")
        aux.reset_index(inplace=True)
        aux.rename(columns={"index": "Date"}, inplace=True)
        try:
            dataset_details = alphacast.datasets.create(dataset_name, repo_id)
            dataset_id = dataset_details["id"]
        except KeyError:
            dataset_id = alphacast.datasets.read_by_name(dataset_name)["id"]
        alphacast.datasets.dataset(dataset_id).initialize_columns(dateColumnName="Date",
                                                                             entitiesColumnNames=["country"],
                                                                             dateFormat="%Y-%m-%d")
        alphacast.datasets.dataset(dataset_id).upload_data_from_df(aux,
                                                                   deleteMissingFromDB=False,
                                                                   onConflictUpdateDB=True,
                                                                   uploadIndex=False)

    return

if __name__ == "__main__":
    upload_public_datasets()
    upload_private_datasets()
    #upload_test_datasets()
