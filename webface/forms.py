from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    # HiddenField,
    # IntegerField,
    SubmitField,
    # FieldList,
    # FormField,
    # Field,
    # RadioField,
)
from wtforms.validators import InputRequired

# from wtforms.widgets import HTMLString


class LoginForm(FlaskForm):
    login = StringField("name", validators=[InputRequired()])
    passwd = PasswordField("passwd", validators=[InputRequired()])
    remember_me = BooleanField("remember_me", default=False)
    submit = SubmitField("login_me")
