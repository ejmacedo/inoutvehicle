from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required
from datetime import datetime, timezone, date
from app.security import bp
from app.models import VehicleRequest, RequestStatus, Role
from app.extensions import db
from app.decorators import role_required


@bp.route('/dashboard')
@login_required
@role_required(Role.SECURITY)
def dashboard():
    filter_date = request.args.get('date', date.today().isoformat())
    try:
        selected_date = date.fromisoformat(filter_date)
    except ValueError:
        selected_date = date.today()
        filter_date = selected_date.isoformat()

    start = datetime(selected_date.year, selected_date.month, selected_date.day, 0, 0, 0)
    end = datetime(selected_date.year, selected_date.month, selected_date.day, 23, 59, 59)

    vehicle_requests = (
        VehicleRequest.query
        .filter(
            VehicleRequest.status == RequestStatus.APPROVED,
            VehicleRequest.departure_datetime >= start,
            VehicleRequest.departure_datetime <= end,
        )
        .order_by(VehicleRequest.departure_datetime.asc())
        .all()
    )

    return render_template(
        'security/dashboard.html',
        title='Portaria — Controle de Saídas',
        vehicle_requests=vehicle_requests,
        filter_date=filter_date,
    )


@bp.route('/solicitacao/<int:request_id>/saiu', methods=['POST'])
@login_required
@role_required(Role.SECURITY)
def mark_departed(request_id):
    vehicle_request = VehicleRequest.query.get_or_404(request_id)
    if not vehicle_request.is_approved():
        abort(400)

    odometer_raw = request.form.get('odometer', '').strip()
    if not odometer_raw or not odometer_raw.isdigit() or int(odometer_raw) <= 0:
        flash('Informe a quilometragem atual do veículo antes de registrar a saída.', 'warning')
        return redirect(url_for('security.dashboard',
                                date=vehicle_request.departure_datetime.date().isoformat()))

    vehicle_request.odometer_departure = int(odometer_raw)
    vehicle_request.actual_departure_datetime = datetime.now(timezone.utc)
    db.session.commit()
    flash(f'Saída de {vehicle_request.employee.full_name} registrada às '
          f'{vehicle_request.actual_departure_datetime.strftime("%H:%M")} '
          f'— Odômetro: {int(odometer_raw):,} km.', 'success')
    return redirect(url_for('security.dashboard',
                            date=vehicle_request.departure_datetime.date().isoformat()))


@bp.route('/solicitacao/<int:request_id>/voltou', methods=['POST'])
@login_required
@role_required(Role.SECURITY)
def mark_returned(request_id):
    vehicle_request = VehicleRequest.query.get_or_404(request_id)
    if not vehicle_request.actual_departure_datetime:
        flash('Registre a saída antes de registrar o retorno.', 'warning')
        return redirect(url_for('security.dashboard',
                                date=vehicle_request.departure_datetime.date().isoformat()))
    vehicle_request.actual_return_datetime = datetime.now(timezone.utc)
    db.session.commit()
    flash(f'Retorno de {vehicle_request.employee.full_name} registrado às '
          f'{vehicle_request.actual_return_datetime.strftime("%H:%M")}.', 'success')
    return redirect(url_for('security.dashboard',
                            date=vehicle_request.departure_datetime.date().isoformat()))
