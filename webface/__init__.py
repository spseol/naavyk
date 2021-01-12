from flask import Flask
from flask_pony import Pony
from flask_login import LoginManager
from flask_misaka import Misaka

# from flask_misaka import Misaka
from flask_wtf.csrf import CSRFProtect
from flask_uuid import FlaskUUID
from pony.orm import set_sql_debug
from base64 import b64encode


def b64e(data):
    return b64encode(data).decode("ascii")


app = Flask(__name__, instance_relative_config=True)
app.config.from_object("config")
app.config.from_pyfile("config.py", silent=True)
app.add_template_filter(b64e)

pony = Pony(app)
misaka = Misaka(
    app, escape=True, autolink=True, highlight=True, strikethrough=True
)
login_manager = LoginManager(app)
login_manager.login_view = "login"  # funkce pro url_for
login_manager.login_message = "Nejprve je třeba se přihlásit :-)"
# login_manager.session_protection = "strong"

# misaka = Misaka(app)
csrf = CSRFProtect(app)
flaskuuid = FlaskUUID(app)

from . import routes
from . import models
from . import forms

if app.env == "development":
    set_sql_debug(True)
    app.config["ADMINS"] = app.config["DEVELOPADMINS"]

pony.connect()
