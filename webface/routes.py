from . import app
from flask import render_template, request, redirect, url_for, session
import functools

# from werkzeug.security import check_password_hash

slova = ("Super", "Perfekt", "Úža", "Flask")


def prihlasit(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if "user" in session:
            return function(*args, **kwargs)
        else:
            return redirect(url_for("login", url=request.path))

    return wrapper


@app.route("/", methods=["GET"])
def index():
    return render_template("base.html.j2")


@app.route("/info/")
def info():
    return render_template("info.html.j2")


@app.route("/abc/")
def abc():
    return render_template("abc.html.j2", slova=slova)


@app.route("/text/")
def text():
    return """

<h1>Text</h1>

<p>toto je text</p>

"""
