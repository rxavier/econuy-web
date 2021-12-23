from sqlalchemy import inspect
from flask import render_template
from flask import current_app as app


@app.route("/", methods=["GET", "POST"])
def landing():
    return render_template("landing.html")


@app.route("/sobre", methods=["GET"])
def about():
    return render_template("about.html")
