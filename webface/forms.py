from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    TextAreaField,
    HiddenField,
    IntegerField,
    SubmitField,
    # FieldList,
    # FormField,
    # Field,
    # RadioField,
    # Label,
    widgets,
    SelectMultipleField,
)
from wtforms.validators import (
    InputRequired,
    optional,
    length,
    Regexp,
    ValidationError,
    DataRequired,
    NumberRange,
    URL,
)
from werkzeug.utils import secure_filename
from pony.orm import db_session
from .models import Group


# from wtforms.widgets import HTMLString


class FilenameRegexp(Regexp):
    def __call__(self, form, field, message=None):
        if field.data is None:
            return True  # jméno souboru neexistuje, soubory nebyl vybrán
        filename = secure_filename(field.data.filename)
        search = self.regex.search(filename or "")
        if not search:
            if message is None:
                if self.message is None:
                    message = field.gettext("Wrong FileName " + filename)
                else:
                    message = self.message

            raise ValidationError(message)
        return search


class MaybeURL(URL):
    def __call__(self, form, field):
        if field.data == "":
            return
        super().__call__(form, field)


class LoginForm(FlaskForm):
    login = StringField("name", validators=[InputRequired()])
    passwd = PasswordField("passwd", validators=[InputRequired()])
    remember_me = BooleanField("remember_me", default=False)
    submit = SubmitField("login_me")


class GroupForm(FlaskForm):
    """Přidání skupiny"""

    name = StringField("name", validators=[InputRequired()])
    description = TextAreaField(
        "description", validators=[optional(), length(max=777)]
    )
    submit = SubmitField("addgroup")


class GroupEdit(FlaskForm):
    """Nastavení atributů skupiny"""

    # group_id = HiddenField("group_id", validators=[DataRequired()])
    group_id = HiddenField("group_id")
    enable = SubmitField("Povolit ✓")
    disable = SubmitField("Zakázat ✗")
    lock = SubmitField("Zamknout 🔒")
    unlock = SubmitField("Odemknout 🔓")
    remove = SubmitField("Smazat")


# class CheckBox(FlaskForm):
#     checkbox = BooleanField()


class MultiCheckboxField(SelectMultipleField):
    # widget = widgets.ListWidget(prefix_label=False)
    widget = widgets.ListWidget()
    option_widget = widgets.CheckboxInput()


class ItemForm(FlaskForm):
    """Přidání položky"""

    name = StringField("name", validators=[InputRequired()])
    description = TextAreaField(
        "description", validators=[optional(), length(max=777)]
    )
    url = StringField("url", validators=[MaybeURL()])
    price = IntegerField(
        "price",
        validators=[
            InputRequired(),
            NumberRange(
                min=0, max=777, message="Zadej číslo v intervalu 0 až 777"
            ),
        ],
    )
    necessary = BooleanField("necessary", default=False)
    recommended = BooleanField("recommended", default=False)
    # groups = FieldList(FormField(CheckBox))
    groups = MultiCheckboxField(
        validators=[DataRequired("Musí být vybrána alespoň jedna skupina")]
    )
    imgdata = FileField(
        "Obrázek",
        validators=[
            FileRequired(),
            FilenameRegexp(r"\.(jpe?g|png|gif|svg|webp)$"),
        ],
    )
    submit = SubmitField("additem")

    @db_session
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.groups.choices = []
        self.enablegroups = []
        for i, g in enumerate(Group.select().order_by(Group.name)):
            self.groups.choices.append((str(g.id), g.name))
            if g.enable:
                self.enablegroups.append(i)


class ItemOperation(FlaskForm):
    "smazání položky"
    iid = HiddenField("iid")
    remove = SubmitField("Smazat")
    edit = SubmitField("Editovat")


class ItemEdit(ItemForm):
    imgdata = FileField(
        "Obrázek", validators=[FilenameRegexp(r"\.(jpe?g|png|gif|svg|webp)$")],
    )


class OrderForm(FlaskForm):
    """objednávka"""

    iid = HiddenField("iid")
    count = IntegerField(
        "count",
        validators=[
            InputRequired(),
            NumberRange(
                min=0, max=777, message="Zadej číslo v intervalu 0 až 777"
            ),
        ],
    )
    update = SubmitField("Aktualizovat")

    # def __init__(self, *args, **kwargs):
    #     self.iid.type = False
    #     self.count.type = False
