import os
from pathlib import Path

from dotenv import load_dotenv

from econuy_web.tasks import get_project_root

load_dotenv(Path(get_project_root(), ".env"))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_BINDS = {"queries": os.environ.get("QUERY_DATABASE_URL")}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EXPORT_FOLDER = os.environ.get("EXPORT_FOLDER")
