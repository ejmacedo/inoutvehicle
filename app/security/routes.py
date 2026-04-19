from flask import render_template, request
from flask_login import login_required
from app.security import bp
from app.models import VehicleRequest, RequestStatus
from app.decorators import role_required
from app.models import Role
from datetime import datetime, timezone, date


@bp.route('/dashboard')
@login_required
@role_required(Role.SECURITY)
def dashboard():
    filter_date = request.args.get('date', date.today().isoformat())
    filter_status = request.args.get('status', 'all')

    try:
        selected_date = date.fromisoformat(filter_date)
    except ValueError:
        selected_date = date.today()

    query = VehicleRequest.query

    if filter_status != 'all':
        query = query.filter(VehicleRequest.status == filter_status)
    else:
        query = query.filter(VehicleRequest.status == RequestStatus.APPROVED)

    start = datetime(selected_date.year, selected_date.month, selected_date.day, 0, 0, 0)
    end = datetime(selected_date.year, selected_date.month, selected_date.day, 23, 59, 59)
    query = query.filter(
        VehicleRequest.departure_datetime >= start,
        VehicleRequest.departure_datetime <= end,
    )

    vehicle_requests = query.order_by(VehicleRequest.departure_datetime.asc()).all()

    return render_template('security/dashboard.html',
                           title='Portaria - Controle de Saídas',
                           vehicle_requests=vehicle_requests,
                           filter_date=filter_date,
                           filter_status=filter_status)
