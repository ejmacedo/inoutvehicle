from flask import Blueprint

bp = Blueprint('coordinator', __name__, url_prefix='/coordenador')

from app.coordinator import routes  # noqa: E402, F401
