import sys
import os

# Add the path to the directory containing your project
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_path)

from econuy.session import Session
from econuy.utils import sql as sqlutil

from econuy_web import db, create_app

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    s = Session(location=db.engine)
    if len(sys.argv) == 1:
        s.get_bulk("all")
        s.get("_monthly_interpolated_gdp")
        s.decompose(component="trend", method="x13", force_x13=True, select="labor_rates_persons")
        sqlutil.df_to_sql(
            s.datasets["labor_rates_persons"],
            name="labor_rates_persons_seas",
            con=db.engine,
        )
    elif sys.argv[1] == "labor_seas":
        s.get("labor_rates_persons")
        s.decompose(component="trend", method="x13", force_x13=True, select="labor_rates_persons")
        sqlutil.df_to_sql(
            s.datasets["labor_rates_persons"],
            name="labor_rates_persons_seas",
            con=db.engine,
        )
    else:
        for arg in sys.argv[1:]:
            s.get(arg)
