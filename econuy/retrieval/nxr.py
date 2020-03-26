import datetime as dt
from os import PathLike, mkdir, path
from pathlib import Path
from typing import Union, Optional

import pandas as pd
from pandas.tseries.offsets import MonthEnd

from econuy.resources import updates, columns
from econuy.resources.lstrings import nxr_url, nxr_daily_url


def get_monthly(update: Union[str, PathLike, None] = None,
                revise_rows: Union[str, int] = "nodup",
                save: Union[str, PathLike, None] = None,
                force_update: bool = False,
                name: Optional[str] = None) -> pd.DataFrame:
    """Get monthly nominal exchange rate data.

    Parameters
    ----------
    update : str, os.PathLike or None, default None
        Path or path-like string pointing to a directory where to find a CSV
        for updating, or ``None``, don't update.
    revise_rows : {'nodup', 'auto', int}
        Defines how to process data updates. An integer indicates how many rows
        to remove from the tail of the dataframe and replace with new data.
        String can either be ``auto``, which automatically determines number of
        rows to replace from the inferred data frequency, or ``nodup``,
        which replaces existing periods with new data.
    save : str, os.PathLike or None, default None
        Path or path-like string pointing to a directory where to save the CSV,
        or ``None``, don't save.
    force_update : bool, default False
        If ``True``, fetch data and update existing data even if it was
        modified within its update window(for nominal exchange rates, 25 days).
    name : str, default None
        CSV filename for updating and/or saving.

    Returns
    -------
    Monthly nominal exchange rates : pd.DataFrame
        Sell rate, monthly average and end of period.

    """
    update_threshold = 25
    if name is None:
        name = "nxr"

    if update is not None:
        update_path = (Path(update) / name).with_suffix(".csv")
        delta, previous_data = updates._check_modified(update_path)

        if delta < update_threshold and force_update is False:
            print(f"{update_path} was modified within {update_threshold} "
                  f"day(s). Skipping download...")
            return previous_data

    nxr_raw = pd.read_excel(nxr_url, skiprows=4, index_col=0, usecols="A,C,F")
    nxr = nxr_raw.dropna(how="any", axis=0)
    nxr.columns = ["Tipo de cambio venta, fin de período",
                   "Tipo de cambio venta, promedio"]
    nxr.index = nxr.index + MonthEnd(1)
    nxr = nxr.apply(pd.to_numeric, errors="coerce")

    if update is not None:
        nxr = updates._revise(new_data=nxr, prev_data=previous_data,
                              revise_rows=revise_rows)

    columns._setmeta(nxr, area="Precios y salarios", currency="-",
                     inf_adj="No", index="No", seas_adj="NSA",
                     ts_type="-", cumperiods=1)

    if save is not None:
        save_path = (Path(save) / name).with_suffix(".csv")
        if not path.exists(path.dirname(save_path)):
            mkdir(path.dirname(save_path))
        nxr.to_csv(save_path)

    return nxr


def get_daily(update: Union[str, PathLike, None] = None,
              save: Union[str, PathLike, None] = None,
              name: Optional[str] = None) -> pd.DataFrame:
    """Get daily nominal exchange rate data.

    Parameters
    ----------
    update : str, os.PathLike or None, default None
        Path or path-like string pointing to a directory where to find a CSV
        for updating, or ``None``, don't update.
    save : str, os.PathLike or None, default None
        Path or path-like string pointing to a directory where to save the CSV,
        or ``None``, don't save.
    name : str, default None
        CSV filename for updating and/or saving.

    Returns
    -------
    Monthly nominal exchange rates : pd.DataFrame
        Sell rate, monthly average and end of period.

    """
    if name is None:
        name = "nxr_daily"

    start_date = dt.datetime(1999, 12, 31)

    if update is not None:
        update_path = (Path(update) / name).with_suffix(".csv")
        prev_data = pd.read_csv(update_path, index_col=0,
                                header=list(range(9)),
                                float_precision="high")
        columns._setmeta(prev_data)
        prev_data.index = pd.to_datetime(prev_data.index)
        start_date = prev_data.index[len(prev_data) - 1]

    today = dt.datetime.now()
    runs = (today - start_date).days // 30
    data = []
    if runs > 0:
        for i in range(1, runs + 1):
            from_ = (start_date + dt.timedelta(days=1)).strftime('%d/%m/%Y')
            to_ = (start_date + dt.timedelta(days=30)).strftime('%d/%m/%Y')
            dates = f"%22FechaDesde%22:%22{from_}%22,%22FechaHasta%22:%22{to_}"
            url = f"{nxr_daily_url}{dates}%22,%22Grupo%22:%222%22}}" + "}"
            try:
                data.append(pd.read_excel(url))
                start_date = dt.datetime.strptime(to_, '%d/%m/%Y')
            except TypeError:
                pass
    from_ = (start_date + dt.timedelta(days=1)).strftime('%d/%m/%Y')
    to_ = dt.datetime.now().strftime('%d/%m/%Y')
    dates = f"%22FechaDesde%22:%22{from_}%22,%22FechaHasta%22:%22{to_}"
    url = f"{nxr_daily_url}{dates}%22,%22Grupo%22:%222%22}}" + "}"
    data.append(pd.read_excel(url))

    output = pd.concat(data, axis=0)
    output = output.pivot(index="Fecha", columns="Moneda",
                          values="Venta").rename_axis(None)
    output.index = pd.to_datetime(output.index, format="%d/%m/%Y",
                                  errors="coerce")
    output.sort_index(inplace=True)
    output.replace(",", ".", regex=True, inplace=True)
    output.columns = ["Tipo de cambio US$, Cable"]
    output = output.apply(pd.to_numeric, errors="coerce")

    columns._setmeta(output, area="Precios y salarios", currency="-",
                     inf_adj="No", index="No", seas_adj="NSA",
                     ts_type="-", cumperiods=1)
    output.columns.set_levels(["-"], level=2, inplace=True)

    if update is not None:
        output = pd.concat([prev_data, output])

    if save is not None:
        save_path = (Path(save) / name).with_suffix(".csv")
        if not path.exists(path.dirname(save_path)):
            mkdir(path.dirname(save_path))
        output.to_csv(save_path)

    return output
