from flask import redirect, url_for
from flask_login import current_user, login_required
from app.main import bp
from app.models import Role


@bp.route('/')
@login_required
def index():
    if current_user.role == Role.ADMIN:
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == Role.COORDINATOR:
        return redirect(url_for('coordinator.dashboard'))
    elif current_user.role == Role.SECURITY:
        return redirect(url_for('security.dashboard'))
    else:
        return redirect(url_for('employee.dashboard'))
