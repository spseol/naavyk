from pony.orm import db_session
from webface.models import Uzivatel
from werkzeug.security import generate_password_hash, check_password_hash

login = input('zadej jmeno > ')
heslo = input('zadej heslo > ')

with db_session:
    uzivatel1 = Uzivatel(login=login, heslo=generate_password_hash(heslo))
