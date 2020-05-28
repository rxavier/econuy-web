from typing import Union, List

from sqlalchemy.engine.base import Connection, Engine
from sqlalchemy import inspect


def full_update(con: Union[Connection, Engine],
                functions: List) -> List:
    output = []
    for f in functions:
        output.append(f(update_loc=con, save_loc=con))
    return output


def clear_tables(con: Union[Connection, Engine]):
    for table in inspect(con).get_table_names():
        if table.startswith("export_"):
            con.engine.execute(f'DROP TABLE IF EXISTS "{table}"')

    return
