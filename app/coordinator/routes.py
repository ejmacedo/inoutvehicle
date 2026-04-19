from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.coordinator import bp
from app.models import VehicleRequest, RequestStatus, Role, User
from app.extensions import db
from app.decorators import role_required
from datetime import datetime, timezone


@bp.route('/dashboard')
@login_required
@role_required(Role.COORDINATOR)
def dashboard():
    subordinate_ids = [u.id for u in current_user.subordinates]
    pending = VehicleRequest.query.filter(
        VehicleRequest.employee_id.in_(subordinate_ids),
        VehicleRequest.status == RequestStatus.PENDING,
    ).order_by(VehicleRequest.created_at.asc()).all()

    history = VehicleRequest.query.filter(
        VehicleRequest.employee_id.in_(subordinate_ids),
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
    _assert_coordinator_owns(vehicle_request)

    notes = request.form.get('notes', '').strip()
    vehicle_request.status = RequestStatus.APPROVED
    vehicle_request.coordinator_notes = notes
    vehicle_request.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    flash('Solicitação aprovada com sucesso.', 'success')
    return redirect(url_for('coordinator.dashboard'))


@bp.route('/solicitacao/<int:request_id>/recusar', methods=['POST'])
@login_required
@role_required(Role.COORDINATOR)
def reject(request_id):
    vehicle_request = VehicleRequest.query.get_or_404(request_id)
    _assert_coordinator_owns(vehicle_request)

    notes = request.form.get('notes', '').strip()
    if not notes:
        flash('É necessário informar o motivo da recusa.', 'danger')
        return redirect(url_for('coordinator.dashboard'))

    vehicle_request.status = RequestStatus.REJECTED
    vehicle_request.coordinator_notes = notes
    vehicle_request.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    flash('Solicitação recusada.', 'warning')
    return redirect(url_for('coordinator.dashboard'))


def _assert_coordinator_owns(vehicle_request):
    subordinate_ids = [u.id for u in current_user.subordinates]
    if vehicle_request.employee_id not in subordinate_ids:
        from flask import abort
        abort(403)
