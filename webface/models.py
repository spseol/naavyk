# from datetime import datetime
from pony.orm import PrimaryKey, Required, Optional, Database  # , Set


db = Database()
db.bind(provider="sqlite", filename="./database.sqlite", create_db=True)


class Uzivatel(db.Entity):
    id = PrimaryKey(int, auto=True)
    login = Required(str)
    password = Required(str)
    email = Optional(str)


db.generate_mapping(create_tables=True)
