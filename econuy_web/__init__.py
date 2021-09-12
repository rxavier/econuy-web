from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

from config import Config


db = SQLAlchemy()
bootstrap = Bootstrap()


def create_app():
    """Initialize the core application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bootstrap.init_app(app)

    with app.app_context():
        from econuy_web import visualization_dash, overview_dash
        from econuy_web.dash_apps.visualization import visualization
        from econuy_web.dash_apps.monitor import monitor
        from econuy_web import routes, update, tasks, clear, errors
        app = visualization.add_dash(app)
        app = monitor.add_dash(app)
        app = overview_dash.add_dash(app)
        app = visualization_dash.add_dash(app)

        return app
