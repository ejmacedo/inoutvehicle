from flask import Blueprint

bp = Blueprint('profile', __name__, url_prefix='/conta')

from app.profile import routes  # noqa: E402, F401
