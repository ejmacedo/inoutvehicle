from flask import Blueprint

bp = Blueprint('privacy', __name__)

from app.privacy import routes  # noqa: E402, F401
