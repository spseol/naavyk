from . import app
from flask import render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, current_user, login_required
from .forms import LoginForm
from .models import User
from pony.orm import db_session


@app.route("/", methods=["GET"])
@login_required
def index():
    return render_template("base.html.j2")


@app.route("/login/", methods=["GET", "POST"])
@db_session
def login():
    if current_user.is_authenticated:
        flash("Už jsi přihlášen!")
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        login = form.login.data
        passwd = form.passwd.data
        user = User.get(login=login)
        if not user:
            user = User(login=login, name="Marek", admin=True)
        if login == "nozka" and passwd == "ahoj":
            login_user(user, remember=form.remember_me.data)
            flash("Právě jsi se přihlásil!")
            return redirect(url_for("index"))
        else:
            flash("Špatné přihlašovací údaje!")
    return render_template("login.html.j2", title="LogIn", form=form)


@app.route("/logout/")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("Byl jsi odhlášen!")
    return redirect(url_for("login"))
