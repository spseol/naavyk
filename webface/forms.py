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
    name = StringField("name", validators=[InputRequired()])
    description = TextAreaField(
        "description", validators=[optional(), length(max=777)]
    )
    submit = SubmitField("addgroup")


class GroupEdit(FlaskForm):
    # group_id = HiddenField("group_id", validators=[DataRequired()])
    group_id = HiddenField("group_id")
    enable = SubmitField("Povolit")
    disable = SubmitField("Zakázat")
    remove = SubmitField("Smazat")


# class CheckBox(FlaskForm):
#     checkbox = BooleanField()


class MultiCheckboxField(SelectMultipleField):
    # widget = widgets.ListWidget(prefix_label=False)
    widget = widgets.ListWidget()
    option_widget = widgets.CheckboxInput()


class ItemForm(FlaskForm):
    name = StringField("name", validators=[InputRequired()])
    description = TextAreaField(
        "description", validators=[optional(), length(max=777)]
    )
    url = StringField("url", validators=[MaybeURL()])
    price = IntegerField("price", validators=[InputRequired()])
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
            FilenameRegexp(r"\.(jpe?g|png|gif|svg)$"),
        ],
    )
    submit = SubmitField("additem")

    @db_session
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.groups.choices = [
            (str(g.id), g.name) for g in list(Group.select(lambda g: g.enable))
        ]

    # @db_session
    # def __init__(self, *args, **kwargs):
    #     super(ItemForm, self).__init__(*args, **kwargs)
    #     for g in list(Group.select(lambda g: g.enable)):
    #         self.groups.append_entry()
    #         self.groups[-1].checkbox.id = "group-{}".format(g.id)
    #         self.groups[-1].checkbox.name = "groups-{}-checkbox".format(g.id)
    #         self.groups[-1].checkbox.label = Label(
    #             self.groups[-1].checkbox.id, g.name
    #         )


class ItemOperation(FlaskForm):
    # iid = HiddenField("iid", validators=[InputRequired()])
    iid = HiddenField("iid")
    remove = SubmitField("Smazat")


class OrderForm(FlaskForm):
    # iid = HiddenField("iid", validators=[InputRequired()])
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
