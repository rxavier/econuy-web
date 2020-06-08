import warnings
from typing import Union, List

from sqlalchemy.engine.base import Connection, Engine
from sqlalchemy import inspect


def full_update(con: Union[Connection, Engine],
                functions: List, **kwargs) -> List:
    output = []
    for f in functions:
        try:
            output.append(f(update_loc=con, save_loc=con, **kwargs))
        except:
            # This exception is intentionally broad.
            # If any function fails, carry on with the next one.
            warnings.warn(f"{f.__module__} failed.")
            continue
    return output


def clear_tables(con: Union[Connection, Engine]):
    for table in inspect(con).get_table_names():
        if table.startswith("export_"):
            con.engine.execute(f'DROP TABLE IF EXISTS "{table}"')

    return
