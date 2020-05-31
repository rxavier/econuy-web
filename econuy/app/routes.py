from random import sample
from string import ascii_letters

from sqlalchemy.exc import ProgrammingError
from flask import (render_template, redirect, url_for,
                   session, make_response, flash)

from econuy import transform
from econuy.app import app, db
from econuy.app.form import SubmitForm, OrderForm
from econuy.utils import sqlutil


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def submit():
    # for key in ["request", "transformations"]:
    # session.pop(key, None)

    form = SubmitForm()
    if form.validate_on_submit():
        indicator_choices = dict(form.indicator.choices)
        frequency_choices = dict(form.frequency.choices)
        operation_res_choices = dict(form.operation_res.choices)
        operation_choices = dict(form.operation.choices)
        chg_diff_type_choices = dict(form.chg_diff_type.choices)
        chg_diff_period_choices = dict(form.chg_diff_period.choices)
        seas_type_choices = dict(form.seas_type.choices)
        session["request"] = {
            "indicator": {
                "data": form.indicator.data,
                "label": indicator_choices[form.indicator.data]},
            "start": {
                "data": fix_date(form.start.data),
                "label": form.start.label},
            "end": {
                "data": fix_date(form.end.data),
                "label": form.end.label},
            "usd": {"data": form.usd.data,
                    "label": form.usd.label},
            "real": {"data": form.real.data,
                     "label": form.real.label},
            "real_start": {"data": fix_date(form.real_start.data),
                           "label": form.real_start.label},
            "real_end": {"data": fix_date(form.real_end.data),
                         "label": form.real_end.label},
            "gdp": {"data": form.gdp.data,
                    "label": form.gdp.label},
            "freq": {"data": form.freq.data,
                     "label": form.freq.label},
            "frequency": {"data": form.frequency.data,
                          "label": frequency_choices[form.frequency.data]},
            "operation_res": {"data": form.operation_res.data,
                              "label": operation_res_choices[
                                  form.operation_res.data]},
            "cum": {"data": form.cum.data,
                    "label": form.cum.label},
            "periods": {"data": form.periods.data,
                        "label": form.periods.label},
            "operation": {"data": form.operation.data,
                          "label": operation_choices[form.operation.data]},
            "base_index": {"data": form.base_index.data,
                           "label": form.base_index.label},
            "base_index_start": {"data": fix_date(form.base_index_start.data),
                                 "label": form.base_index_start.label},
            "base_index_end": {"data": fix_date(form.base_index_end.data),
                               "label": form.base_index_end.label},
            "base_index_base": {"data": form.base_index_base.data,
                                "label": form.base_index_base.label},
            "chg_diff": {"data": form.chg_diff.data,
                         "label": form.chg_diff.label},
            "chg_diff_type": {"data": form.chg_diff_type.data,
                              "label": chg_diff_type_choices[
                                  form.chg_diff_type.data]},
            "chg_diff_period": {"data": form.chg_diff_period.data,
                                "label": chg_diff_period_choices[
                                    form.chg_diff_period.data]},
            "seas": {"data": form.seas.data,
                     "label": form.seas.label},
            "seas_type": {"data": form.seas_type.data,
                          "label": seas_type_choices[form.seas_type.data]}
        }
        transformations = [k for k, v in session["request"].items()
                           if v["data"] is True]
        if len(transformations) > 1:
            return redirect(url_for("order"))
        elif len(transformations) == 1:
            session["transformations"] = {1: transformations[0]}
            return redirect(url_for("query"))
        else:
            session["transformations"] = {}
            return redirect(url_for("query"))
    return render_template("index.html", form=form)


@app.route("/sobre", methods=["GET"])
def about():
    return render_template("about.html")


@app.route("/orden", methods=["GET", "POST"])
def order():
    transformations = [k for k, v in session["request"].items()
                       if v["data"] is True]
    form = OrderForm()
    orders = [(str(i), str(i)) for i in range(1, 9)]
    order_count = orders[:len(transformations)]
    form.usd_order.choices = order_count
    form.real_order.choices = order_count
    form.gdp_order.choices = order_count
    form.freq_order.choices = order_count
    form.cum_order.choices = order_count
    form.base_index_order.choices = order_count
    form.chg_diff_order.choices = order_count
    form.seas_order.choices = order_count
    if form.validate_on_submit():
        order_submit = {
            "usd": form.usd_order.data,
            "real": form.real_order.data,
            "gdp": form.gdp_order.data,
            "freq": form.freq_order.data,
            "cum": form.cum_order.data,
            "base_index": form.base_index_order.data,
            "chg_diff": form.chg_diff_order.data,
            "seas": form.seas_order.data
        }
        pruned_order = {k: v for k, v in order_submit.items()
                        if k in transformations}
        aux = sorted(pruned_order, key=pruned_order.get)
        session["transformations"] = dict(zip(list(range(len(aux))), aux))
        return redirect(url_for("query"))
    return render_template("order.html", form=form,
                           transformations=transformations)


@app.route("/consulta", methods=["GET"])
def query():
    data = {k: {"label": v["label"], "data": empty_to_none(v["data"])}
            for k, v in session["request"].items()}
    indicator = data["indicator"]["data"]
    indicator_label = data["indicator"]["label"]
    function_dict = {
        "usd": lambda x: transform.convert_usd(x, update_loc=db.engine,
                                               only_get=True),
        "real": lambda x: transform.convert_real(
            x, update_loc=db.engine, only_get=True,
            start_date=data["real_start"]["data"],
            end_date=data["real_end"]["data"]
        ),
        "gdp": lambda x: transform.convert_gdp(x, update_loc=db.engine,
                                               only_get=True),
        "freq": lambda x: transform.resample(x,
                                             target=data["frequency"]["data"],
                                             operation=data["operation_res"][
                                                 "data"]),
        "cum": lambda x: transform.rolling(x, periods=data["periods"]["data"],
                                           operation=data["operation"][
                                               "data"]),
        "base_index": lambda x: transform.base_index(
            x, start_date=data["base_index_start"]["data"],
            end_date=data["base_index_end"]["data"],
            base=data["base_index_base"]["data"]),
        "chg_diff": lambda x: transform.chg_diff(
            x, operation=data["chg_diff_type"]["data"],
            period_op=data["chg_diff_period"]["data"]),
        "seas": lambda x: transform.decompose(x,
                                              flavor=data["seas_type"]["data"])
    }
    output = sqlutil.read(con=db.engine, table_name=indicator,
                          start_date=session["request"]["start"]["data"],
                          end_date=session["request"]["end"]["data"])
    if len(session["transformations"]) > 0:
        for t in session["transformations"].values():
            output = function_dict[t](output)
    session["table"] = "export_" + "".join(sample(ascii_letters, 12))
    sqlutil.df_to_sql(output, name=session["table"], con=db.engine)
    transf_parameters = [data[i]["label"] for i in
                         session["transformations"].values()]
    return render_template("query.html", indicator_label=indicator_label,
                           tables=[output.to_html(header="true",
                                                  float_format=lambda x:
                                                  '{:,.1f}'.format(x))],
                           transformations=transf_parameters)


@app.route("/exportar", methods=["GET"])
def export():
    try:
        data = sqlutil.read(con=db.engine, table_name=session["table"])
    except ProgrammingError:
        return flash("La tabla ya no está disponible para descargar. "
                     "Intente la consulta nuevamente.")
    db.engine.execute(f'DROP TABLE IF EXISTS "{session["table"]}"')
    db.engine.execute(f'DROP TABLE IF EXISTS "{session["table"]}_metadata"')
    response = make_response(data.to_csv())
    response.headers["Content-Type"] = "text/csv"
    response.headers[
        "content-disposition"] = "attachment; filename=econuy-export.csv"
    return response


def empty_to_none(choice):
    if choice is "":
        return None
    else:
        return choice


def fix_date(choice):
    if choice is not None:
        return choice.strftime("%Y-%m-%d")
    else:
        return choice
