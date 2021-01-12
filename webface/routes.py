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
    jsonify,
)
from flask_login import (
    login_user,
    logout_user,
    current_user,
    login_required,
)
from .forms import (
    LoginForm,
    GroupForm,
    GroupEdit,
    ItemForm,
    ItemOperation,
    ItemEdit,
    OrderForm,
    OrdersListForm,
    StatusForm,
)
from .models import User, Group, Item, Order, ItemOrder, Classroom
from pony.orm import db_session, ObjectNotFound, desc
import pony.orm as pony
from ldap3 import Server, Connection, ALL, NTLM
from unicodedata import normalize


@app.route("/", methods=["GET"])
@login_required
@db_session
def index():
    groups = Group.select(lambda g: g.enable).sort_by(Group.name)[:]
    user = User[current_user.id]
    for index, g in enumerate(groups):
        items = list(user.orders.select(lambda o: o.group.id == g.id))
        # je třeba ošetři případ, kdy ještě zatím není nic objednáno
        items = items[-1].items if items else []

        groups[index].price = pony.sum(i.item.price * i.count for i in items)
        groups[index].totalcount = pony.count(i for i in items if i.count)

        order = user.orders.select(lambda o: o.group.id == g.id)
        if order and groups[index].totalcount != 0:
            groups[index].status = list(order)[-1].status
        else:
            groups[index].status = None

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

        # server = Server("pdc.spseol.cz", get_info=ALL)
        server = Server(app.config["LDAP"]["host"], get_info=ALL)
        conn = Connection(
            server,
            user="spseol.cz\\{}".format(login),
            password=passwd,
            authentication=NTLM,
        )
        if app.env == "development" or conn.bind():
            if app.env == "development":
                name = login
                login = "." + login
                classname = "develop"
            else:
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
                    classname = m.group(1)
                else:
                    classname = "XxX"
                name = conn.entries[-1].cn.value
            user = User.get(login=login)
            admin = login in app.config["ADMINS"]
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
            conn.unbind()
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
    "Seznam skupin. Skupiny lze vytvářet, mazat, povolovat a zamykat"
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
            Group(name=name, description=description, enable=True, lock=False)
            flash("Skupina >{}< byla přidána".format(name))
        return redirect(url_for("group"))

    edform = GroupEdit()
    if edform.validate_on_submit():
        if edform.enable.data:
            Group[edform.group_id.data].enable = True
        if edform.disable.data:
            Group[edform.group_id.data].enable = False
        if edform.lock.data:
            Group[edform.group_id.data].lock = True
        if edform.unlock.data:
            Group[edform.group_id.data].lock = False
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
    "Vložení nové položky (zboží)."
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
    # groups = Group.select(lambda g: g.enable)[:]
    groups = Group.select().order_by(Group.name)[:]
    return render_template("item.html.j2", groups=groups, addform=addform)


@app.route("/group/<uuid:gid>", methods=["GET"])
@login_required
@db_session
def item_in_group(gid):
    """Výpis všech položek ve skupině s možností editace a smazání."""
    if not current_user.admin:
        flash("Nemáš dostatečná oprávnění!")
        return redirect(url_for("index"))
    try:
        group = Group[gid]
        items = group.items.order_by(Item.name)
        # počty položek v jednotlivých skupinách
        counts = [dict() for _ in range(len(items))]
        for index, item in enumerate(items):
            counts[index]["users"] = []
            counts[index]["users_"] = []
            for io in item.orders.sort_by(
                lambda io: (
                    desc(io.order.status),
                    io.order.group.name,
                    io.order.user.classroom.name,
                    io.order.user.name,
                )
            ):
                if io.count > 0:
                    if io.order.group == group:
                        counts[index]["users"].append(
                            (
                                io.order.user.classroom.name,
                                io.order.user.name,
                                io.order.status,
                                io.order.id,
                                io.count,
                            )
                        )
                    else:
                        counts[index]["users_"].append(
                            (
                                io.order.user.classroom.name,
                                io.order.user.name,
                                io.order.status,
                                io.order.id,
                                io.count,
                                io.order.group.name,
                            )
                        )

            # status == ordered
            counts[index]["ordered"] = pony.sum(
                io.count
                for io in item.orders
                if io.order.status in ("ordered", "")
                and io.order.group == group
            )
            # status == ordered -- napříč skupinami
            counts[index]["ordered_"] = pony.sum(
                io.count
                for io in item.orders
                if io.order.status in ("ordered", "")
            )
            # status == paid
            counts[index]["paid"] = pony.sum(
                io.count
                for io in item.orders
                if io.order.status == "paid" and io.order.group == group
            )
            # status == paid -- napříč skupinami
            counts[index]["paid_"] = pony.sum(
                io.count for io in item.orders if io.order.status == "paid"
            )
            # status == handedover
            counts[index]["handedover"] = pony.sum(
                io.count
                for io in item.orders
                if io.order.status == "handedover" and io.order.group == group
            )
            # status == handedover  -- napříč skupinami
            counts[index]["handedover_"] = pony.sum(
                io.count
                for io in item.orders
                if io.order.status == "handedover"
            )
        opform = ItemOperation()
        return render_template(
            "item_in_group.html.j2",
            group=group,
            items=items[:],
            counts=counts,
            opform=opform,
        )
    except ObjectNotFound:
        return abort(404)


@app.route("/group/<uuid:gid>", methods=["POST"])
@login_required
@db_session
def item_in_group_POST(gid):
    """Smazání položky.
    Editace se řeší AJAXem pomocí funkce itemedit."""
    if not current_user.admin:
        flash("Nemáš dostatečná oprávnění!")
        return redirect(url_for("index"))
    opform = ItemOperation()
    if opform.validate_on_submit() and opform.remove.data:
        iid = opform.iid.data
        try:
            item = Item[iid]
            item.delete()
            return redirect(url_for("item_in_group", gid=gid))
        except ObjectNotFound:
            return abort(404)
    return redirect(url_for("item_in_group", gid=gid))


@app.route("/item/<uuid:iid>", methods=["GET", "POST"])
@login_required
@db_session
def itemedit(iid):
    """Editace položky. Slouží pro AJAX požadavky.
    GET vrátí HTML s formulářem. Slouží pro AJAX fetch
    POST se také volá AJAXem a slouží pro změny
    JS kód je v item_in_group.html.j2"""
    if not current_user.admin:
        flash("Nemáš dostatečná oprávnění!")
        return abort(403)
        return redirect(url_for("index"))
    try:
        item = Item[iid]
    except ObjectNotFound:
        return abort(404)
    form = ItemEdit()
    if request.method == "GET":
        form.name.data = item.name
        form.description.data = item.description
        form.url.data = item.url
        form.price.data = item.price
        form.necessary.data = item.necessary
        form.recommended.data = item.recommended
        form.groups.data = [str(g.id) for g in item.groups]
        # print(form.groups.data)
        return render_template("itemedit.html.j2", form=form, item=item)
    elif request.method == "POST":
        if form.validate():
            if form.imgdata.data:
                f = form.imgdata.data
                item.imgdata = bytes(f.read())
                item.imgtype = f.mimetype
                image = True
            else:
                image = False
            item.name = form.name.data
            item.description = form.description.data
            item.url = form.url.data
            item.price = int(form.price.data)
            item.necessary = form.necessary.data
            item.recommended = form.recommended.data
            for gid in form.groups.data:
                item.groups += [Group[gid]]
            return jsonify(
                name=item.name,
                description=item.description,
                url=item.url,
                price=item.price,
                necessary=item.necessary,
                recommended=item.recommended,
                image=image,
            )
        else:
            print(form.errors)
            return jsonify(form.errors), 400


@app.route("/order/<uuid:gid>", methods=["GET", "POST"])
@login_required
@db_session
def order(gid):
    """Objednávka. Ukazuje a aktualizuje počty objednaných položek.
    Funguje i bez AJAXu, ale AJAX funguje také pomocí funkce orderAJAX. """
    try:
        group = Group[gid]
    except ObjectNotFound:
        return abort(404)
    if not group.enable:
        flash(
            "Tato skupina není v tuto chvíli dostupná. "
            " Platnost stránky vypršela.",
            "error",
        )
        return redirect(url_for("index"))

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
    user = User[current_user.id]
    items = list(user.orders.select(lambda o: o.group.id == gid))
    # je třeba ošetři případ, kdy ještě zatím není nic objednáno
    items = items[-1].items if items else []
    counts = dict()
    for i in items:
        counts[i.item.id] = i.count
    price = pony.sum(i.item.price * i.count for i in items)
    count = pony.count(i for i in items if i.count)
    order = (
        Order.get(user=user, group=group)
        or Order(user=user, group=group, done=False),
    )

    return render_template(
        "order.html.j2",
        group=group,
        counts=counts,
        Item=Item,
        form=form,
        price=price,
        count=count,
        status=list(order)[-1].status,
    )


@app.route("/orderAJAX/<uuid:gid>", methods=["POST"])
@login_required
@db_session
def orderAJAX(gid):
    try:
        group = Group[gid]
    except ObjectNotFound:
        return abort(404)
    if not group.enable:
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
            if not group.lock:
                item_order.count = count
            else:
                count = item_order.count
        else:
            if not group.lock:
                ItemOrder(order=order, item=item, count=count)
            else:
                ItemOrder(order=order, item=item, count=0)
                count = 0

        items = list(user.orders.select(lambda o: o.group.id == gid))
        # je třeba ošetři případ, kdy ještě zatím není nic objednáno
        items = items[-1].items if items else []

        price = pony.sum(i.item.price * i.count for i in items)
        totalcount = pony.count(i for i in items if i.count)

        return jsonify(count=count, price=price, totalcount=totalcount)
    else:
        return abort(405)


@app.route("/orders/", methods=["GET"])
@login_required
def orders():
    """Seznam objednávek. SPA -> ordersAJAXlist
    Objednávky se dají označit jako zaplacené, vydané, hotové."""
    if not current_user.admin:
        flash("Nemáš dostatečná oprávnění!")
        return abort(403)
    ordersform = OrdersListForm()
    statusform = StatusForm()
    return render_template(
        "orders.html.j2", ordersform=ordersform, statusform=statusform
    )


@app.route("/ordersAJAX/list/", methods=["POST"])
@login_required
@db_session
def ordersAJAXlist():
    if not current_user.admin:
        return abort(403)
    form = OrdersListForm()
    if not form.validate_on_submit():
        abort(400)
    orders = pony.select(
        (
            o,
            pony.count(i for i in o.items if i.count > 0),
            pony.sum(o.items.item.price * o.items.count),
        )
        for o in Order
        if pony.sum(o.items.item.price * o.items.count) > 0
    ).sort_by(
        lambda o, c, s: (
            o.status,
            o.group.name,
            o.user.classroom.name,
            o.user.name,
        )
    )
    result = []
    for o, c, s in orders:
        one = dict()
        one["status"] = o.status if o.status else "ordered"
        one["order_id"] = o.id
        one["group_id"] = o.group.id
        one["group"] = o.group.name
        one["user"] = o.user.name
        one["classroom"] = o.user.classroom.name
        one["totalprice"] = s
        one["itemcount"] = c
        result.append(one)
    return jsonify(orders=result)


@app.route("/ordersAJAX/status/", methods=["POST"])
@login_required
@db_session
def ordersAJAXstatus():
    if not current_user.admin:
        return abort(403)
    status = request.json.get("status")
    oid = request.json.get("oid")
    order = Order.get(id=oid)
    if not order:
        abort(404)
    if status in ("ordered", "paid", "handedover", "done"):
        order.status = status
    else:
        return abort(400)
    if status == "ordered":
        pass
    return jsonify(True)


@app.route("/orders/<uuid:oid>", methods=["GET"])
@login_required
@db_session
def order_detail(oid):
    """Detail každé jedné objednávky"""
    if not current_user.admin:
        flash("Nemáš dostatečná oprávnění!")
        return abort(403)
    order = Order.get(id=oid)
    if not order:
        return abort(404)
    items = order.items.select(lambda io: io.count > 0).sort_by(
        lambda io: io.item.name
    )
    return render_template(
        "order_detail.html.j2",
        items=items,
        order=order,
        totalcount=pony.count(io for io in items if io.count),
        totalprice=pony.sum(io.item.price * io.count for io in items),
    )


############################################################################


# @app.route("/myajax.js")
# def myajaxjs():
#     gid = request.args.get("gid")
#     return render_template("myajax.js", gid=gid)


@app.route("/img/<uuid:iid>")
@login_required
@db_session
def img(iid):
    try:
        item = Item[iid]
    except ObjectNotFound:
        return abort(404)
    response = make_response(item.imgdata)
    response.headers.set("Content-Type", item.imgtype)
    response.headers.set(
        "Content-Disposition",
        "inline",
        filename="{}.{}".format(
            normalize("NFKD", item.name.replace(" ", "_")).encode(
                "latin-1", "ignore"
            ),
            item.imgtype.replace("/", "."),
        )
        # "Content-Disposition", "attachment", filename="%s.jpg" % _id
    )
    return response


@app.errorhandler(404)
def page_not_found(error):
    # print(error.code)
    # print(error.name)
    # print(error.description)
    return render_template("404-samson.html", e=error), 404


@app.errorhandler(500)
def internal_server_error(error):
    # print(error.code)
    # print(error.name)
    # print(error.description)
    return render_template("500-samson.html", e=error), 500
