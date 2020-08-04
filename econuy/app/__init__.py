from typing import Union

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from sqlalchemy import MetaData
from sqlalchemy.engine.base import Connection, Engine

from econuy.config import Config
from econuy.app.app_strings import table_options


db = SQLAlchemy()
bootstrap = Bootstrap()


def create_app():
    """Initialize the core application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bootstrap.init_app(app)

    with app.app_context():
        from econuy.app import (routes, errors, form, tasks,
                                update, clear, dashapp)
        app = dashapp.add_dash(app, options=get_all_indicators(db.engine))

        return app


def get_all_indicators(con: Union[Connection, Engine]):
    meta = MetaData()
    meta.reflect(bind=con)
    datas = meta.sorted_tables
    all_cols = {}
    for table in datas:
        if not (table.name.endswith("_metadata") or
                table.name in ["lin_gdp", "commodity_prices",
                               "commodity_weights", "public_debt_assets",
                               "table_labor_nsa", "fiscal_pe"]):
            all_cols.update({table.name: [col.key.__str__() for col in table.columns
                                          if col.key != "index"]})
    output = []
    for k in all_cols.keys():
        for col in all_cols[k]:
            output.append({"label": f"{table_options[k]} - {col}",
                           "value": f"{k}>{col}"})

    return output
