from econuy.retrieval import (cpi, fiscal_accounts, commodity_index,
                              labor, national_accounts, nxr, rxr, reserves)
from econuy.frequent import (labor_rate_people, inflation, fiscal,
                             labor_real_wages)
from econuy.app import db
from econuy.app.tasks import full_update


if __name__ == "__main__":
    full_update(con=db.engine,
                functions=[cpi.get,
                           fiscal_accounts.get,
                           commodity_index.get,
                           labor.get_rates,
                           labor.get_wages,
                           national_accounts.get,
                           nxr.get_daily,
                           nxr.get_monthly,
                           rxr.get_official,
                           rxr.get_custom,
                           reserves.get_changes,
                           labor_rate_people,
                           inflation,
                           labor_real_wages])
    fiscal(update_loc=db.engine, save_loc=db.engine,
           aggregation="gps", fss=True)
    fiscal(update_loc=db.engine, save_loc=db.engine,
           aggregation="nfps", fss=True)
    fiscal(update_loc=db.engine, save_loc=db.engine,
           aggregation="gc", fss=True)
