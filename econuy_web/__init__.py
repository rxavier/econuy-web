from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

from config import Config
from econuy_web.app_strings import table_options


db = SQLAlchemy()
bootstrap = Bootstrap()


def create_app():
    """Initialize the core application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bootstrap.init_app(app)

    with app.app_context():
        from econuy_web import form
        from econuy_web import update
        from econuy_web import dashapp
        from econuy_web import tasks
        from econuy_web import clear
        from econuy_web import errors
        from econuy_web import routes
        app = dashapp.add_dash(app)

        return app
