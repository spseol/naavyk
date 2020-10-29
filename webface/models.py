# from datetime import datetime
from pony.orm import PrimaryKey, Required, Optional, Set
from flask_login import UserMixin
from pony.orm import db_session
from uuid import UUID, uuid4

# Import Flask-Pony instance from __init__.py module
from . import pony, login_manager

# Get a reference to the base class of Pony entities
db = pony.db


@login_manager.user_loader
@db_session
def user_loader(user_id):
    try:
        user = User[UUID(user_id)]
        user.classname = user.classroom.name
    except ValueError:
        user = None
    return user


class User(UserMixin, db.Entity):
    # id = PrimaryKey(int, auto=True)
    id = PrimaryKey(UUID, default=uuid4)
    login = Required(str)
    name = Required(str)
    classroom = Required("Classroom")
    admin = Required(bool)
    orders = Set("Order")


class Classroom(db.Entity):
    id = PrimaryKey(UUID, default=uuid4)
    name = Required(str, unique=True)
    users = Set(User)


class Item(db.Entity):
    # id = PrimaryKey(int, auto=True)
    id = PrimaryKey(UUID, default=uuid4)
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
    id = PrimaryKey(UUID, default=uuid4)
    name = Required(str, unique=True)
    enable = Required(bool)
    description = Optional(str)
    items = Set(Item)
    orders = Set("Order")


class Order(db.Entity):
    # id = PrimaryKey(int, auto=True)
    id = PrimaryKey(UUID, default=uuid4)
    user = Required(User)
    done = Required(bool)
    items = Set("ItemOrder")
    group = Required(Group)


class ItemOrder(db.Entity):
    order = Required("Order")
    item = Required(Item)
    PrimaryKey(item, order)
    count = Required(int)
