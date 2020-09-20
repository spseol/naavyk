# from datetime import datetime
from pony.orm import PrimaryKey, Required, Optional, Set, buffer
from flask_login import UserMixin
from pony.orm import db_session

# Import Flask-Pony instance from __init__.py module
from . import pony, login_manager

# Get a reference to the base class of Pony entities
db = pony.db


@login_manager.user_loader
@db_session
def user_loader(user_id):
    user = User[int(user_id)]
    return user


class User(UserMixin, db.Entity):
    id = PrimaryKey(int, auto=True)
    login = Required(str)
    name = Required(str)
    classroom = Optional(str)
    admin = Required(bool)
    orders = Set("Order")


class Item(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    img = Required(buffer)
    desctiption = Optional(str)
    groups = Set("Group")
    price = Required(int)
    necessary = Required(bool)
    recommended = Required(bool)
    order = Set("Order")


class Group(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    description = Optional(str)
    items = Set(Item)
    orders = Set("Order")


class Order(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    items = Set(Item)
    group = Required(Group)
