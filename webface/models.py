# from datetime import datetime
from pony.orm import PrimaryKey, Required, Optional, Set
from flask_login import UserMixin
from pony.orm import db_session

# Import Flask-Pony instance from __init__.py module
from . import pony, login_manager

# Get a reference to the base class of Pony entities
db = pony.db


@login_manager.user_loader
@db_session
def user_loader(user_id):
    try:
        user = User[int(user_id)]
    except ValueError:
        user = None
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
    imgdata = Required(bytes)
    imgtype = Required(str)
    description = Optional(str)
    url = Optional(str)
    groups = Set("Group")
    price = Required(int)
    necessary = Required(bool)
    recommended = Required(bool)
    orderes = Set("ItemOrder")


class Group(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    enable = Required(bool)
    description = Optional(str)
    items = Set(Item)
    orders = Set("Order")


class Order(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    done = Required(bool)
    items = Set("ItemOrder")
    group = Required(Group)


class ItemOrder(db.Entity):
    order = Required("Order")
    item = Required(Item)
    PrimaryKey(item, order)
    count = Required(int)
