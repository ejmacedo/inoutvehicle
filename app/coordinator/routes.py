from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime, timezone
from app.coordinator import bp
from app.models import VehicleRequest, RequestStatus, Role
from app.extensions import db
from app.decorators import role_required
from app.email_utils import notify_employee_approved, notify_employee_rejected


@bp.route('/dashboard')
@login_required
@role_required(Role.COORDINATOR)
def dashboard():
    employee_ids = [u.id for u in current_user.employees]
    pending = VehicleRequest.query.filter(
        VehicleRequest.employee_id.in_(employee_ids),
        VehicleRequest.status == RequestStatus.PENDING,
    ).order_by(VehicleRequest.created_at.asc()).all()

    history = VehicleRequest.query.filter(
        VehicleRequest.employee_id.in_(employee_ids),
        VehicleRequest.status != RequestStatus.PENDING,
    ).order_by(VehicleRequest.created_at.desc()).limit(50).all()

    return render_template('coordinator/dashboard.html',
                           title='Painel do Coordenador',
                           pending=pending,
                           history=history)


@bp.route('/solicitacao/<int:request_id>/aprovar', methods=['POST'])
@login_required
@role_required(Role.COORDINATOR)
def approve(request_id):
    vehicle_request = VehicleRequest.query.get_or_404(request_id)
    _check_ownership(vehicle_request)

    notes = request.form.get('notes', '').strip()
    vehicle_request.status = RequestStatus.APPROVED
    vehicle_request.coordinator_notes = notes
    vehicle_request.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    notify_employee_approved(vehicle_request)
    flash('Solicitação aprovada com sucesso.', 'success')
    return redirect(url_for('coordinator.dashboard'))


@bp.route('/solicitacao/<int:request_id>/recusar', methods=['POST'])
@login_required
@role_required(Role.COORDINATOR)
def reject(request_id):
    vehicle_request = VehicleRequest.query.get_or_404(request_id)
    _check_ownership(vehicle_request)

    notes = request.form.get('notes', '').strip()
    if not notes:
        flash('É necessário informar o motivo da recusa.', 'danger')
        return redirect(url_for('coordinator.dashboard'))

    vehicle_request.status = RequestStatus.REJECTED
    vehicle_request.coordinator_notes = notes
    vehicle_request.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    notify_employee_rejected(vehicle_request)
    flash('Solicitação recusada.', 'warning')
    return redirect(url_for('coordinator.dashboard'))


def _check_ownership(vehicle_request):
    employee_ids = [u.id for u in current_user.employees]
    if vehicle_request.employee_id not in employee_ids:
        abort(403)
