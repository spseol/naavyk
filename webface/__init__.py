import flask
from flask_misaka import Misaka

app = flask.Flask(__name__)
Misaka(app)
app.secret_key = b"totoj e zceLa n@@@hodny retezec nejlep os.urandom(24)"
app.secret_key = (
    b"x6\x87j@\xd3\x88\x0e8\xe8pM\x13\r\xafa\x8b\xdbp\x8a\x1f\xd41\xb8"
)

from . import routes
from . import models
