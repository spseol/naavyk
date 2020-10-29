import re
from . import app
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    make_response,
    abort,
)
from flask_login import login_user, logout_user, current_user, login_required
from .forms import (
    LoginForm,
    GroupForm,
    GroupEdit,
    ItemForm,
    ItemOperation,
    OrderForm,
)
from .models import User, Group, Item, Order, ItemOrder, Classroom
from pony.orm import db_session, ObjectNotFound
from ldap3 import Server, Connection, ALL, NTLM


@app.route("/", methods=["GET"])
@login_required
@db_session
def index():
    groups = Group.select(lambda g: g.enable).sort_by(Group.name)[:]
    return render_template("base.html.j2", groups=groups)


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

        server = Server("pdc.spseol.cz", get_info=ALL)
        conn = Connection(
            server,
            user="spseol.cz\\{}".format(login),
            password=passwd,
            authentication=NTLM,
        )
        if conn.bind():
            conn.search(
                "dc=spseol,dc=cz",
                "(sAMAccountName={})".format(login),
                attributes=["cn", "distinguishedName"],
            )
            m = re.search(
                "OU=([1234]([ABCL]|V[TE]))",
                conn.entries[-1].distinguishedName.value.upper(),
            )
            if m:
                classname = m.groups(1)
            else:
                classname = "XxX"
            name = conn.entries[-1].cn.value
            user = User.get(login=login)
            admin = login == "nozka"
            classroom = Classroom.get(name=classname) or Classroom(
                name=classname
            )
            if user:
                user.name = name
                user.classroom = classroom
                user.admin = admin
            else:
                user = User(
                    login=login, name=name, admin=admin, classroom=classroom
                )
                user = User.get(
                    login=login
                )  # nevím přesně proč, ale tohle je potřeba udělat
            login_user(user, remember=form.remember_me.data)
            flash("Právě jsi se přihlásil!")
            next_ = request.args.get("next")
            if next_:
                print(next_)
                return redirect(next_)
            else:
                return redirect(url_for("index"))
        else:
            flash("Špatné přihlašovací údaje!")
            return redirect(url_for("login"))
    return render_template("login.html.j2", title="LogIn", form=form)


@app.route("/logout/")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("Byl jsi odhlášen!")
    return redirect(url_for("login"))


@app.route("/group/", methods=["GET", "POST"])
@login_required
@db_session
def group():
    if not current_user.admin:
        flash("Nemáš dostatečná oprávnění!")
        return redirect(url_for("index"))

    addform = GroupForm()
    if addform.validate_on_submit():
        name = addform.name.data
        description = addform.description.data
        group = Group.get(name=name)
        if group:
            flash(
                'Chyba: skupina "{}" již existuje! Sorry.'.format(name),
                "error",
            )
        else:
            Group(name=name, description=description, enable=True)
            flash("Skupina >{}< byla přidána".format(name))
        return redirect(url_for("group"))

    edform = GroupEdit()
    if edform.validate_on_submit():
        if edform.enable.data:
            Group[edform.group_id.data].enable = True
        if edform.disable.data:
            Group[edform.group_id.data].enable = False
        if edform.remove.data:
            Group[edform.group_id.data].delete()

    groups = Group.select().order_by(Group.name)[:]
    return render_template(
        "group.html.j2", groups=groups, addform=addform, edform=edform
    )


@app.route("/item/", methods=["GET", "POST"])
@login_required
@db_session
def item():
    if not current_user.admin:
        flash("Nemáš dostatečná oprávnění!")
        return redirect(url_for("index"))

    addform = ItemForm()
    if addform.validate_on_submit():
        f = addform.imgdata.data
        # print(addform.groups.data)
        item = Item(
            name=addform.name.data,
            imgdata=bytes(f.read()),
            imgtype=f.mimetype,
            description=addform.description.data,
            url=addform.url.data,
            price=int(addform.price.data),
            necessary=addform.necessary.data,
            recommended=addform.recommended.data,
        )
        for gid in addform.groups.data:
            item.groups += [Group[gid]]

        flash("Nová položka byla vložena", "ok")
        return redirect(url_for("item"))
    else:
        if addform.is_submitted():
            for field, message in addform.errors.items():
                flash("Chybička: {}->{}".format(field, message), "error")
    groups = Group.select(lambda g: g.enable)[:]
    return render_template("item.html.j2", groups=groups, addform=addform)


@app.route("/group/<uuid:gid>", methods=["GET"])
@login_required
@db_session
def item_in_group(gid):
    if not current_user.admin:
        flash("Nemáš dostatečná oprávnění!")
        return redirect(url_for("index"))
    try:
        group = Group[gid]
        opform = ItemOperation()
        return render_template(
            "item_in_group.html.j2", group=group, opform=opform, Item=Item
        )
    except ObjectNotFound:
        return abort(404)


@app.route("/group/<uuid:gid>", methods=["POST"])
@login_required
@db_session
def item_in_group_POST(gid):
    if not current_user.admin:
        flash("Nemáš dostatečná oprávnění!")
        return redirect(url_for("index"))
    opform = ItemOperation()
    if opform.validate_on_submit():
        iid = opform.iid.data
        try:
            item = Item[iid]
            item.delete()
            return redirect(url_for("item_in_group", gid=gid))
        except ObjectNotFound:
            return abort(404)


@app.route("/order/<uuid:gid>", methods=["GET", "POST"])
@login_required
@db_session
def order(gid):
    try:
        group = Group[gid]
    except ObjectNotFound:
        return abort(404)

    form = OrderForm()
    if form.validate_on_submit():
        count = form.count.data
        try:
            item = Item[form.iid.data]
            user = User[current_user.id]
        except ObjectNotFound:
            return abort(404)
        order = Order.get(user=user, group=group) or Order(
            user=user, group=group, done=False
        )
        item_order = ItemOrder.get(order=order, item=item)
        if item_order:
            item_order.count = count
        else:
            ItemOrder(order=order, item=item, count=count)
        return redirect(url_for("order", gid=gid))
    # objednané položky
    items = list(current_user.orders.select(lambda o: o.group.id == gid))
    # je třeba ošetři případ, kdy ještě zatím není nic objednáno
    items = items[-1].items if items else []
    counts = dict()
    for i in items:
        counts[i.item.id] = i.count
    return render_template(
        "order.html.j2", group=group, counts=counts, Item=Item, form=form
    )


@app.route("/orderAJAX/<uuid:gid>", methods=["POST"])
@login_required
@db_session
def orderAJAX(gid):
    try:
        group = Group[gid]
    except ObjectNotFound:
        return abort(404)

    form = OrderForm()
    if form.validate_on_submit():
        count = form.count.data
        try:
            item = Item[form.iid.data]
            user = User[current_user.id]
        except ObjectNotFound:
            return abort(404)
        order = Order.get(user=user, group=group) or Order(
            user=user, group=group, done=False
        )
        item_order = ItemOrder.get(order=order, item=item)
        if item_order:
            item_order.count = count
        else:
            ItemOrder(order=order, item=item, count=count)
        return str(count)
    else:
        return abort(405)


############################################################################


@app.route("/myajax.js")
def myajaxjs():
    gid = request.args.get("gid")
    return render_template("myajax.js", gid=gid)


@app.route("/img/<uuid:iid>")
@login_required
@db_session
def img(iid):
    item = Item[iid]
    response = make_response(item.imgdata)
    response.headers.set("Content-Type", item.imgtype)
    response.headers.set(
        "Content-Disposition",
        "inline",
        filename="{}.{}".format(
            item.name.replace(" ", "_"), item.imgtype.replace("/", ".")
        )
        # "Content-Disposition", "attachment", filename="%s.jpg" % _id
    )
    return response


@app.errorhandler(404)
def page_not_found(error):
    # print(error.code)
    # print(error.name)
    # print(error.description)
    return render_template("404.html", e=error), 404
