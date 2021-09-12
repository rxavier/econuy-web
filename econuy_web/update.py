import sys

from econuy.session import Session
from econuy.utils import sqlutil

from econuy_web import db, create_app

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    s = Session(location=db.engine)
    if len(sys.argv) == 1:
        s.get_bulk("all")
        s.get("_lin_gdp")
        s.decompose(component="trend", method="x13", force_x13=True, select="labor_rates_people")
        sqlutil.df_to_sql(s.datasets["labor_rates_people"], name="labor_rates_people_seas",
                          con=db.engine)
    else:
        for arg in sys.argv[1:]:
            s.get(arg)
