from flask import Blueprint

bp = Blueprint('security', __name__, url_prefix='/portaria')

from app.security import routes  # noqa: E402, F401
