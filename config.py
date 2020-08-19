import os

from dotenv import load_dotenv

load_dotenv("econuy_web/.env")


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_BINDS = {"queries": os.environ.get("QUERY_DATABASE_URL")}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
