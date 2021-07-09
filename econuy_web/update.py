import sys

from econuy.session import Session

from econuy_web import db, create_app

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    s = Session(location=db.engine)
    if len(sys.argv) == 1:
        s.get_bulk("all")
        s.get("_lin_gdp")
    else:
        for arg in sys.argv[1:]:
            s.get(arg)
