from flask import Flask
from flask_pony import Pony
from flask_login import LoginManager
from flask_misaka import Misaka


app = Flask(__name__, instance_relative_config=True)
app.config.from_object("config")
app.config.from_pyfile("config.py", silent=True)

pony = Pony(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"  # funkce pro url_for
login_manager.login_message = "Nejprve je třeba se přihlásit :-)"
# login_manager.session_protection = "strong"

misaka = Misaka(app)

from . import routes
from . import models
from . import forms

pony.connect()
