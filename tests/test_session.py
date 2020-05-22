import shutil
from os import listdir, remove, path
from typing import Tuple
from pathlib import Path

import pandas as pd
import pytest

from econuy import transform
from econuy.utils import metadata
from econuy.utils.lstrings import fiscal_metadata
from econuy.retrieval import nxr
from econuy.session import Session
from .test_transform import dummy_df

CUR_DIR = path.abspath(path.dirname(__file__))
TEST_DIR = path.join(path.dirname(CUR_DIR), "test-data")


def remove_clutter(avoid: Tuple[str] = ("fx_ff.csv", "fx_spot_ff.csv",
                                        "reserves_chg.csv",
                                        "commodity_weights.csv",
                                        "nxr_daily.csv")):
    [remove(path.join(TEST_DIR, x)) for x in listdir(TEST_DIR)
     if x not in avoid]
    return


def test_prices_inflation():
    remove_clutter()
    session = Session(location=TEST_DIR)
    assert isinstance(session, Session)
    assert isinstance(session.dataset, pd.DataFrame)
    inflation = session.get_frequent(dataset="inflation").dataset
    remove_clutter()
    prices = session.get(dataset="cpi").dataset
    remove_clutter()
    inter = transform.chg_diff(prices, period_op="inter")
    compare = inflation.iloc[:, [1]]
    inter.columns = compare.columns
    assert compare.equals(inter)
    monthly = transform.chg_diff(prices, period_op="last")
    compare = inflation.iloc[:, [2]]
    monthly.columns = compare.columns
    assert compare.equals(monthly)
    trend, seasadj = transform.decompose(prices, trading=True, outlier=False)
    monthly_sa = transform.chg_diff(seasadj)
    compare = inflation.iloc[:, [3]]
    monthly_sa.columns = compare.columns
    assert compare.equals(monthly_sa)
    monthly_trend = transform.chg_diff(trend)
    compare = inflation.iloc[:, [4]]
    monthly_trend.columns = compare.columns
    assert monthly_trend.equals(monthly_trend)
    remove_clutter()


def test_fiscal():
    remove_clutter()
    session = Session(location=TEST_DIR)
    assert isinstance(session, Session)
    assert isinstance(session.dataset, pd.DataFrame)
    fiscal_tfm = session.get_frequent(dataset="fiscal", aggregation="nfps",
                                      fss=True, unit="gdp").dataset
    remove_clutter()
    fiscal_ = session.get(dataset="fiscal").dataset
    nfps = fiscal_["nfps"]
    gc = fiscal_["gc-bps"]
    proc = pd.DataFrame(index=nfps.index)
    proc["Ingresos: SPNF-SPC"] = nfps["Ingresos: SPNF"]
    proc["Egresos: Primarios SPNF-SPC"] = nfps["Egresos: Primarios SPNF"]
    proc["Egresos: Inversiones SPNF-SPC"] = nfps["Egresos: Inversiones"]
    proc["Intereses: SPNF"] = nfps["Intereses: Totales"]
    proc["Egresos: Totales SPNF"] = (proc["Egresos: Primarios SPNF-SPC"]
                                     + proc["Intereses: SPNF"])
    proc["Resultado: Primario intendencias"] = nfps[
        "Resultado: Primario intendencias"
    ]
    proc["Resultado: Primario BSE"] = nfps["Resultado: Primario BSE"]
    proc["Resultado: Primario SPNF"] = nfps["Resultado: Primario SPNF"]
    proc["Resultado: Global SPNF"] = nfps["Resultado: Global SPNF"]

    proc["Ingresos: FSS"] = gc["Ingresos: FSS"]
    proc["Intereses: FSS"] = gc["Intereses: BPS-FSS"]
    proc["Ingresos: SPNF-SPC aj. FSS"] = (proc["Ingresos: SPNF-SPC"]
                                          - proc["Ingresos: FSS"])
    proc["Intereses: SPNF aj. FSS"] = (proc["Intereses: SPNF"]
                                       - proc["Intereses: FSS"])
    proc["Egresos: Totales SPNF aj. FSS"] = (proc["Egresos: Totales SPNF"]
                                             - proc["Intereses: FSS"])
    proc["Resultado: Primario SPNF aj. FSS"] = (
            proc["Resultado: Primario SPNF"]
            - proc["Ingresos: FSS"])
    proc["Resultado: Global SPNF aj. FSS"] = (proc["Resultado: Global SPNF"]
                                              - proc["Ingresos: FSS"]
                                              + proc["Intereses: FSS"])

    cols = fiscal_metadata["nfps"][True]
    compare = proc.loc[:, cols]
    metadata._set(compare, area="Cuentas fiscales y deuda",
                  currency="UYU", inf_adj="No", unit="No",
                  seas_adj="NSA", ts_type="Flujo", cumperiods=1)
    compare_gdp = transform.rolling(compare, periods=12, operation="sum")
    compare_gdp = transform.convert_gdp(compare_gdp)
    compare_gdp.columns = fiscal_tfm.columns
    assert compare_gdp.equals(fiscal_tfm)
    remove_clutter()
    fiscal_tfm = session.get_frequent(dataset="fiscal", aggregation="nfps",
                                      fss=True, unit="usd").dataset
    compare_usd = transform.convert_usd(compare)
    compare_usd.columns = fiscal_tfm.columns
    assert compare_usd.equals(fiscal_tfm)
    remove_clutter()
    fiscal_tfm = session.get_frequent(dataset="fiscal", aggregation="nfps",
                                      fss=True, unit="real").dataset
    compare_real = transform.convert_real(compare)
    compare_real.columns = fiscal_tfm.columns
    assert compare_real.equals(fiscal_tfm)
    remove_clutter()
    start_date = "2010-01-31"
    end_date = "2010-12-31"
    fiscal_tfm = session.get_frequent(dataset="fiscal", aggregation="nfps",
                                      fss=True, unit="real_usd",
                                      start_date=start_date,
                                      end_date=end_date).dataset
    compare_real_usd = transform.convert_real(compare, start_date=start_date,
                                              end_date=end_date)
    xr = nxr.get_monthly(update_path=None, save_path=None)
    compare_real_usd = compare_real_usd.divide(
        xr[start_date:end_date].mean()[1])
    compare_real_usd.columns = fiscal_tfm.columns
    assert compare_real_usd.equals(fiscal_tfm)
    remove_clutter()
    with pytest.raises(ValueError):
        session.get_frequent(dataset="fiscal", aggregation="nfps",
                             unit="wrong")
    with pytest.raises(ValueError):
        session.get_frequent(dataset="fiscal", aggregation="wrong")
    remove_clutter()


def test_labor():
    remove_clutter()
    session = Session(location=TEST_DIR)
    assert isinstance(session, Session)
    assert isinstance(session.dataset, pd.DataFrame)
    labor_tfm = session.get_frequent(dataset="labor", seas_adj="trend").dataset
    labor_tfm = labor_tfm.iloc[:, [0, 1, 2]]
    remove_clutter()
    labor_ = session.get(dataset="labor").dataset
    labor_trend, labor_sa = transform.decompose(labor_, outlier=True,
                                                trading=True)
    labor_trend.columns = labor_tfm.columns
    assert labor_trend.equals(labor_tfm)
    remove_clutter()
    labor_tfm = session.get_frequent(dataset="labor", seas_adj="seas").dataset
    labor_tfm = labor_tfm.iloc[:, [0, 1, 2]]
    labor_sa.columns = labor_tfm.columns
    assert labor_sa.equals(labor_tfm)
    remove_clutter()
    labor_tfm = session.get_frequent(dataset="labor", seas_adj=None).dataset
    compare = labor_.iloc[:, 0].div(labor_.iloc[:, 1]).round(4)
    compare_2 = labor_tfm.iloc[:, 3].div(labor_tfm.iloc[:, 4]).round(4)
    assert compare.equals(compare_2)
    compare = labor_tfm.iloc[:, 3].mul(labor_.iloc[:, 2]).div(100).round(4)
    assert compare.equals(labor_tfm.iloc[:, 5].round(4))
    remove_clutter()
    with pytest.raises(ValueError):
        session.get_frequent(dataset="labor", seas_adj="wrong")


def test_wages():
    remove_clutter()
    session = Session(location=TEST_DIR)
    assert isinstance(session, Session)
    assert isinstance(session.dataset, pd.DataFrame)
    full_wages = session.get_frequent(dataset="real_wages",
                                      seas_adj="trend").dataset
    wages_tfm = full_wages.iloc[:, [0, 1, 2]]
    remove_clutter()
    wages_ = session.get(dataset="wages").dataset
    wages_trend, wages_sa = transform.decompose(wages_, outlier=False,
                                                trading=True)
    wages_trend = transform.base_index(wages_trend, start_date="2008-07-31")
    wages_trend.columns = wages_tfm.columns
    assert wages_trend.equals(wages_tfm)
    remove_clutter()
    full_wages = session.get_frequent(dataset="wages", seas_adj="seas").dataset
    wages_tfm = full_wages.iloc[:, [0, 1, 2]]
    wages_sa = transform.base_index(wages_sa, start_date="2008-07-31")
    wages_sa.columns = wages_tfm.columns
    assert wages_sa.equals(wages_tfm)
    remove_clutter()
    full_wages = session.get_frequent(dataset="wages", seas_adj=None).dataset
    real_wages = full_wages.iloc[:, [3, 4, 5]]
    compare = transform.convert_real(wages_)
    compare = transform.base_index(compare, start_date="2008-07-31")
    compare.columns = real_wages.columns
    assert real_wages.equals(compare)
    remove_clutter()
    with pytest.raises(ValueError):
        session.get_frequent(dataset="wages", seas_adj="wrong")


def test_naccounts():
    remove_clutter()
    session = Session(location=TEST_DIR)
    assert isinstance(session, Session)
    assert isinstance(session.dataset, pd.DataFrame)
    na_ = session.get(dataset="na").dataset
    assert isinstance(na_, dict)
    assert len(na_) == 6
    remove_clutter()


def test_edge():
    remove_clutter()
    session = Session(location=TEST_DIR)
    assert isinstance(session, Session)
    assert isinstance(session.dataset, pd.DataFrame)
    session.get(dataset="cpi", update=False, save=False)
    with pytest.raises(ValueError):
        session.get(dataset="wrong")
    with pytest.raises(ValueError):
        session.get_frequent(dataset="wrong")
    remove_clutter()
    session = Session(location="new_dir")
    assert path.isdir("new_dir")
    shutil.rmtree(session.location)
    Session(location=TEST_DIR).get_frequent(dataset="inflation",
                                            update=False, save=False)
    remove_clutter()


def test_save():
    remove_clutter()
    data = dummy_df(freq="M")
    session = Session(location=TEST_DIR, dataset=data)
    session.save(name="test_save")
    assert path.isfile(Path(TEST_DIR) / "test_save.csv")
    remove_clutter()
    data = dummy_df(freq="M")
    session = Session(location=TEST_DIR, dataset={
        "data1": data, "data2": data})
    session.save(name="test_save")
    assert path.isfile(Path(TEST_DIR) / "test_save_data1.csv")
    assert path.isfile(Path(TEST_DIR) / "test_save_data2.csv")
    remove_clutter()
    session.location = "new_dir"
    session.save(name="test_save")
    assert path.isfile(Path(session.location) / "test_save_data1.csv")
    assert path.isfile(Path(session.location) / "test_save_data2.csv")
    session.dataset = data
    session.save(name="test_save")
    assert path.isfile(Path(session.location) / "test_save.csv")
    remove_clutter()
    shutil.rmtree(session.location)


def test_logging(caplog):
    remove_clutter()
    caplog.clear()
    Session(location=TEST_DIR, log="test")
    assert path.isfile(path.join(TEST_DIR, "test.log"))
    remove_clutter()
    caplog.clear()
    Session(location=TEST_DIR, log=2)
    assert path.isfile(path.join(TEST_DIR, "info.log"))
    remove_clutter()
    caplog.clear()
    with pytest.raises(ValueError):
        Session(location=TEST_DIR, log=5)
    remove_clutter()
    caplog.clear()
    Session(location=TEST_DIR, log=1)
    assert "Logging method: console" in caplog.text
    assert "Logging method: console and file" not in caplog.text
    assert not path.isfile(path.join(TEST_DIR, "info.log"))
    caplog.clear()
    remove_clutter()
    Session(location=TEST_DIR, log=0)
    assert caplog.text == ""
