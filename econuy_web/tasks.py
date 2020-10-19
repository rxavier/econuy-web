from pathlib import Path
from typing import Union, List

from sqlalchemy.engine.base import Connection, Engine
from sqlalchemy import inspect


def full_update(con: Union[Connection, Engine],
                functions: List) -> List:
    output = []
    for f in functions:
        try:
            name = f.__name__
            module = f.__module__
        except AttributeError:
            name = f.func.__name__
            module = f.func.__module__
        try:
            print(f"Running {name} in {module}...")
            output.append(f(update_loc=con, save_loc=con))
            print("Success.")
        except:
            # This exception is intentionally broad.
            # If any function fails, carry on with the next one.
            print(f"{name} in {module} FAILED.")
            continue
    return output


def clear_tables(con: Union[Connection, Engine]):
    for table in inspect(con).get_table_names():
        if table.startswith("export_"):
            con.engine.execute(f'DROP TABLE IF EXISTS "{table}"')

    return


def get_project_root() -> Path:
    return Path(__file__).parent
