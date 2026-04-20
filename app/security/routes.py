from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required
from datetime import datetime, timezone
from app.security import bp
from app.models import VehicleRequest, DriverReservation, RequestStatus, Role, Vehicle, User
from app.extensions import db
from app.decorators import role_required


def _build_portaria_list(args):
    """Retorna (vr_list, dr_list) aplicando os filtros recebidos."""
    name_q = args.get('name', '').strip()
    vehicle_q = args.get('vehicle_id', '')
    date_q = args.get('date', '')

    # --- VehicleRequests aprovados ---
    vr = VehicleRequest.query.filter(VehicleRequest.status == RequestStatus.APPROVED)
    if name_q:
        vr = vr.join(VehicleRequest.employee).filter(
            User.full_name.ilike(f'%{name_q}%'))
    if vehicle_q:
        vr = vr.filter(VehicleRequest.vehicle_id == int(vehicle_q))
    if date_q:
        try:
            from datetime import date
            d = date.fromisoformat(date_q)
            start = datetime(d.year, d.month, d.day, 0, 0, 0)
            end = datetime(d.year, d.month, d.day, 23, 59, 59)
            vr = vr.filter(VehicleRequest.departure_datetime.between(start, end))
        except ValueError:
            pass

    # --- DriverReservations ---
    dr = DriverReservation.query
    if name_q:
        dr = dr.join(DriverReservation.driver).filter(
            User.full_name.ilike(f'%{name_q}%'))
    if vehicle_q:
        dr = dr.filter(DriverReservation.vehicle_id == int(vehicle_q))
    if date_q:
        try:
            from datetime import date
            d = date.fromisoformat(date_q)
            start = datetime(d.year, d.month, d.day, 0, 0, 0)
            end = datetime(d.year, d.month, d.day, 23, 59, 59)
            dr = dr.filter(DriverReservation.departure_datetime.between(start, end))
        except ValueError:
            pass

    return (vr.order_by(VehicleRequest.departure_datetime.desc()).all(),
            dr.order_by(DriverReservation.departure_datetime.desc()).all())


def _register_obs(obj, scheduled_dt):
    """Gera OBS portaria se saída real diferir >= 30 min da prevista."""
    actual = datetime.now()
    diff_sec = (actual - scheduled_dt).total_seconds()
    diff_min = int(abs(diff_sec) / 60)
    if diff_min >= 30:
        direction = 'antes' if diff_sec < 0 else 'depois'
        obj.portaria_obs = (
            f'Saída registrada {diff_min} minuto(s) {direction} '
            f'do horário previsto ({scheduled_dt.strftime("%H:%M")}).'
        )


@bp.route('/dashboard')
@login_required
@role_required(Role.SECURITY)
def dashboard():
    vr_list, dr_list = _build_portaria_list(request.args)
    vehicles = Vehicle.query.filter_by(is_active=True).order_by(Vehicle.name).all()
    return render_template(
        'security/dashboard.html',
        title='Portaria — Controle de Saídas',
        vr_list=vr_list,
        dr_list=dr_list,
        vehicles=vehicles,
        args=request.args,
    )


# ── VehicleRequest: saída ─────────────────────────────────────────────────────

@bp.route('/solicitacao/<int:request_id>/saiu', methods=['POST'])
@login_required
@role_required(Role.SECURITY)
def mark_departed(request_id):
    vr = VehicleRequest.query.get_or_404(request_id)
    if not vr.is_approved():
        abort(400)
    km = request.form.get('odometer', '').strip()
    if not km or not km.isdigit() or int(km) <= 0:
        flash('Informe a quilometragem atual do veículo para registrar a saída.', 'warning')
        return redirect(url_for('security.dashboard'))
    vr.odometer_departure = int(km)
    vr.actual_departure_datetime = datetime.now()
    _register_obs(vr, vr.departure_datetime)
    db.session.commit()
    flash(f'Saída de {vr.employee.full_name} registrada — {vr.actual_departure_datetime.strftime("%d/%m/%Y %H:%M")}.', 'success')
    return redirect(url_for('security.dashboard', **request.args))


# ── VehicleRequest: retorno ───────────────────────────────────────────────────

@bp.route('/solicitacao/<int:request_id>/voltou', methods=['POST'])
@login_required
@role_required(Role.SECURITY)
def mark_returned(request_id):
    vr = VehicleRequest.query.get_or_404(request_id)
    if not vr.actual_departure_datetime:
        flash('Registre a saída antes do retorno.', 'warning')
        return redirect(url_for('security.dashboard'))
    km = request.form.get('odometer', '').strip()
    if not km or not km.isdigit() or int(km) <= 0:
        flash('Informe a quilometragem do veículo no retorno.', 'warning')
        return redirect(url_for('security.dashboard'))
    vr.odometer_return = int(km)
    vr.actual_return_datetime = datetime.now()
    db.session.commit()
    flash(f'Retorno de {vr.employee.full_name} registrado — {vr.actual_return_datetime.strftime("%d/%m/%Y %H:%M")}.', 'success')
    return redirect(url_for('security.dashboard', **request.args))


# ── DriverReservation: saída ──────────────────────────────────────────────────

@bp.route('/reserva/<int:reservation_id>/saiu', methods=['POST'])
@login_required
@role_required(Role.SECURITY)
def driver_departed(reservation_id):
    dr = DriverReservation.query.get_or_404(reservation_id)
    km = request.form.get('odometer', '').strip()
    if not km or not km.isdigit() or int(km) <= 0:
        flash('Informe a quilometragem atual do veículo para registrar a saída.', 'warning')
        return redirect(url_for('security.dashboard'))
    dr.odometer_departure = int(km)
    dr.actual_departure_datetime = datetime.now()
    _register_obs(dr, dr.departure_datetime)
    db.session.commit()
    flash(f'Saída de {dr.driver.full_name} registrada — {dr.actual_departure_datetime.strftime("%d/%m/%Y %H:%M")}.', 'success')
    return redirect(url_for('security.dashboard', **request.args))


# ── DriverReservation: retorno ────────────────────────────────────────────────

@bp.route('/reserva/<int:reservation_id>/voltou', methods=['POST'])
@login_required
@role_required(Role.SECURITY)
def driver_returned(reservation_id):
    dr = DriverReservation.query.get_or_404(reservation_id)
    if not dr.actual_departure_datetime:
        flash('Registre a saída antes do retorno.', 'warning')
        return redirect(url_for('security.dashboard'))
    km = request.form.get('odometer', '').strip()
    if not km or not km.isdigit() or int(km) <= 0:
        flash('Informe a quilometragem do veículo no retorno.', 'warning')
        return redirect(url_for('security.dashboard'))
    dr.odometer_return = int(km)
    dr.actual_return_datetime = datetime.now()
    db.session.commit()
    flash(f'Retorno de {dr.driver.full_name} registrado — {dr.actual_return_datetime.strftime("%d/%m/%Y %H:%M")}.', 'success')
    return redirect(url_for('security.dashboard', **request.args))
