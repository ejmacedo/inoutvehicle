from flask import Blueprint

bp = Blueprint('reports', __name__, url_prefix='/relatorios')

from app.reports import routes  # noqa: E402, F401
