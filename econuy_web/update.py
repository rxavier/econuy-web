from functools import partial

from econuy.retrieval import (cpi, fiscal_accounts, commodity_index, trade,
                              labor, national_accounts, nxr, rxr, reserves,
                              public_debt, industrial_production, call,
                              deposits, credits, rates, sectors, energy,
                              confidence, risk, income)
from econuy.custom import (labor_rate_people, cpi_measures, fiscal,
                           labor_real_wages, trade_balance, terms_of_trade,
                           core_industrial, net_public_debt, bonds)
from econuy_web import db, create_app
from econuy_web.tasks import full_update

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    updates = full_update(
        con=db.engine,
        functions=[labor.get_hours,
                   energy.get_electricity,
                   energy.get_gasoline,
                   energy.get_diesel,
                   trade.get_containers,
                   sectors.get_cement,
                   sectors.get_milk,
                   sectors.get_cattle,
                   confidence.get_consumer,
                   risk.get_ubi,
                   income.get_household,
                   income.get_capita,
                   call.get,
                   deposits.get,
                   credits.get,
                   fiscal_accounts.get_taxes,
                   rates.get,
                   bonds,
                   cpi.get,
                   public_debt.get,
                   fiscal_accounts.get,
                   commodity_index.get,
                   labor.get_rates,
                   labor.get_wages,
                   industrial_production.get,
                   national_accounts.get,
                   nxr.get_daily,
                   nxr.get_monthly,
                   rxr.get_official,
                   rxr.get_custom,
                   reserves.get,
                   reserves.get_changes,
                   trade.get,
                   labor_rate_people,
                   cpi_measures,
                   labor_real_wages,
                   trade_balance,
                   terms_of_trade,
                   core_industrial,
                   net_public_debt,
                   partial(fiscal, aggregation="gps", fss=True),
                   partial(fiscal, aggregation="nfps", fss=True),
                   partial(fiscal, aggregation="gc", fss=True),
                   partial(national_accounts._lin_gdp, only_get=False,
                           only_get_na=True)]
    )
