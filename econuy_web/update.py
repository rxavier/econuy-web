from functools import partial

from econuy.retrieval import (economic_activity, fiscal_accounts, prices,
                              external_sector, financial_sector,
                              labor, income, international)
from econuy_web import db, create_app
from econuy_web.tasks import full_update

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    updates = full_update(
        con=db.engine,
        functions=[international.gdp,
                   international.stocks,
                   international.policy_rates,
                   international.long_rates,
                   international.currencies,
                   labor.hours,
                   economic_activity.electricity,
                   economic_activity.gasoline,
                   economic_activity.diesel,
                   economic_activity.cement,
                   economic_activity.milk,
                   economic_activity.cattle,
                   income.consumer_confidence,
                   financial_sector.sovereign_risk,
                   income.income_household,
                   income.income_capita,
                   financial_sector.call_rate,
                   financial_sector.deposits,
                   financial_sector.credit,
                   fiscal_accounts.tax_revenue,
                   financial_sector.interest_rates,
                   financial_sector.bonds,
                   prices.cpi,
                   fiscal_accounts.public_debt,
                   fiscal_accounts.balance,
                   external_sector.commodity_index,
                   labor.labor_rates,
                   labor.nominal_wages,
                   labor.real_wages,
                   labor.nominal_wages,
                   economic_activity.industrial_production,
                   economic_activity.national_accounts,
                   prices.nxr_daily,
                   prices.nxr_monthly,
                   external_sector.rxr_official,
                   external_sector.rxr_custom,
                   external_sector.reserves,
                   external_sector.reserves_changes,
                   external_sector.trade,
                   labor.rates_people,
                   prices.cpi_measures,
                   external_sector.trade_balance,
                   external_sector.terms_of_trade,
                   economic_activity.core_industrial,
                   fiscal_accounts.net_public_debt,
                   fiscal_accounts.balance_fss,
                   partial(economic_activity._lin_gdp, only_get=False,
                           only_get_na=True)]
    )
