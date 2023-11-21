from pathlib import Path
from typing import Union

from sqlalchemy.engine.base import Connection, Engine
from sqlalchemy import inspect


def clear_tables(con: Union[Connection, Engine]):
    for table in inspect(con).get_table_names():
        if table.startswith("export_"):
            con.engine.execute(f'DROP TABLE IF EXISTS "{table}"')

    return


def get_project_root() -> Path:
    return Path(__file__).parent.parent
