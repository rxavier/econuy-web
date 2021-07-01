from econuy.session import Session

from econuy_web import db, create_app

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    s = Session(location=db.engine)
    s.get_bulk("all")
    s.get("_lin_gdp")
