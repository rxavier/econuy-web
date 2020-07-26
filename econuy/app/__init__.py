from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

from econuy.config import Config

db = SQLAlchemy()
bootstrap = Bootstrap()


def create_app():
    """Initialize the core application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bootstrap.init_app(app)

    with app.app_context():
        from econuy.app import routes, errors, form, tasks, update, clear

        return app
