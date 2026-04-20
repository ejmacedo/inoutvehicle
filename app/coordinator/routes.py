from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime, timezone
from app.coordinator import bp
from app.coordinator.forms import (ApproveForm, RejectForm, DriverReservationForm,
                                   CoordinatorEditUserForm, CoordinatorCreateDriverForm)
from app.models import VehicleRequest, DriverReservation, RequestStatus, Role, User, Vehicle
from app.extensions import db
from app.decorators import role_required
from app.email_utils import notify_employee_approved, notify_employee_rejected
from app.utils import get_unavailable_vehicle_ids


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_ownership(vehicle_request):
    if vehicle_request.employee_id not in [u.id for u in current_user.employees]:
        abort(403)


def _available_vehicle_choices(exclude_vehicle_id=None):
    """Veículos ativos e disponíveis para seleção."""
    unavailable = get_unavailable_vehicle_ids()
    vehicles = Vehicle.query.filter_by(is_active=True).order_by(Vehicle.name).all()
    choices = []
    for v in vehicles:
        is_unavail = v.id in unavailable
        # Se é o veículo que já está aprovado nesta solicitação, permite mantê-lo
        if is_unavail and v.id != exclude_vehicle_id:
            label = f'{v.name} — {v.plate} ⚠ INDISPONÍVEL'
        else:
            label = f'{v.name} — {v.plate} ({v.model})'
        choices.append((v.id, label))
    return choices, unavailable


# ── Solicitações de funcionários ──────────────────────────────────────────────

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

    unavailable = get_unavailable_vehicle_ids()
    vehicles = Vehicle.query.filter_by(is_active=True).order_by(Vehicle.name).all()

    return render_template('coordinator/dashboard.html',
                           title='Painel do Coordenador',
                           pending=pending,
                           history=history,
                           vehicles=vehicles,
                           unavailable=unavailable)


@bp.route('/solicitacao/<int:request_id>/aprovar', methods=['POST'])
@login_required
@role_required(Role.COORDINATOR)
def approve(request_id):
    vehicle_request = VehicleRequest.query.get_or_404(request_id)
    _check_ownership(vehicle_request)

    new_vehicle_id = request.form.get('vehicle_id', type=int)
    notes = request.form.get('notes', '').strip()

    if not new_vehicle_id:
        flash('Selecione um veículo para aprovar.', 'danger')
        return redirect(url_for('coordinator.dashboard'))

    unavailable = get_unavailable_vehicle_ids()
    if new_vehicle_id in unavailable:
        v = Vehicle.query.get(new_vehicle_id)
        flash(f'O veículo "{v.name}" está indisponível. Escolha outro.', 'danger')
        return redirect(url_for('coordinator.dashboard'))

    # Registra troca de veículo nas notas
    if new_vehicle_id != vehicle_request.vehicle_id:
        old_v = Vehicle.query.get(vehicle_request.vehicle_id)
        new_v = Vehicle.query.get(new_vehicle_id)
        swap_note = f'Veículo alterado pelo coordenador: {old_v.name} → {new_v.name}.'
        notes = f'{swap_note} {notes}'.strip() if notes else swap_note
        vehicle_request.vehicle_id = new_vehicle_id

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


# ── Gerenciamento de funcionários ─────────────────────────────────────────────

@bp.route('/funcionarios')
@login_required
@role_required(Role.COORDINATOR)
def employees():
    emps = current_user.employees
    return render_template('coordinator/employees.html',
                           title='Meus Funcionários', employees=emps)


@bp.route('/funcionarios/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(Role.COORDINATOR)
def edit_employee(user_id):
    user = User.query.get_or_404(user_id)
    # Coordenador só edita seus funcionários e motoristas
    allowed_ids = [u.id for u in current_user.employees] + \
                  [u.id for u in User.query.filter_by(role=Role.DRIVER).all()
                   if current_user in u.coordinators]
    if user.id not in allowed_ids or user.role in (Role.ADMIN, Role.COORDINATOR):
        abort(403)

    form = CoordinatorEditUserForm(original_user=user, obj=user)
    if form.validate_on_submit():
        if (form.username.data != user.username and
                User.query.filter_by(username=form.username.data).first()):
            flash(f'O usuário "{form.username.data}" já está em uso.', 'danger')
        elif (form.email.data != user.email and
              User.query.filter_by(email=form.email.data).first()):
            flash(f'O e-mail "{form.email.data}" já está cadastrado.', 'danger')
        else:
            user.full_name = form.full_name.data
            user.username = form.username.data
            user.email = form.email.data
            user.is_active = form.is_active.data
            if form.password.data:
                user.set_password(form.password.data)
            db.session.commit()
            flash(f'Dados de "{user.full_name}" atualizados.', 'success')
            return redirect(url_for('coordinator.employees'))

    return render_template('coordinator/edit_employee.html',
                           title='Editar Funcionário', form=form, user=user)


# ── Motoristas ────────────────────────────────────────────────────────────────

@bp.route('/motoristas')
@login_required
@role_required(Role.COORDINATOR)
def drivers():
    # Motoristas atribuídos a este coordenador
    all_drivers = User.query.filter_by(role=Role.DRIVER).all()
    my_drivers = [d for d in all_drivers if current_user in d.coordinators]
    return render_template('coordinator/drivers.html',
                           title='Motoristas', drivers=my_drivers)


@bp.route('/motoristas/novo', methods=['GET', 'POST'])
@login_required
@role_required(Role.COORDINATOR)
def create_driver():
    form = CoordinatorCreateDriverForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash(f'O usuário "{form.username.data}" já está em uso.', 'danger')
        elif User.query.filter_by(email=form.email.data).first():
            flash(f'O e-mail "{form.email.data}" já está cadastrado.', 'danger')
        else:
            driver = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                role=Role.DRIVER,
                is_active=form.is_active.data,
            )
            driver.set_password(form.password.data)
            driver.coordinators.append(current_user)
            db.session.add(driver)
            db.session.commit()
            flash(f'Motorista "{driver.full_name}" cadastrado.', 'success')
            return redirect(url_for('coordinator.drivers'))

    return render_template('coordinator/driver_form.html',
                           title='Novo Motorista', form=form)


@bp.route('/motoristas/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(Role.COORDINATOR)
def edit_driver(user_id):
    driver = User.query.get_or_404(user_id)
    if driver.role != Role.DRIVER or current_user not in driver.coordinators:
        abort(403)

    form = CoordinatorEditUserForm(original_user=driver, obj=driver)
    if form.validate_on_submit():
        if (form.username.data != driver.username and
                User.query.filter_by(username=form.username.data).first()):
            flash(f'O usuário "{form.username.data}" já está em uso.', 'danger')
        elif (form.email.data != driver.email and
              User.query.filter_by(email=form.email.data).first()):
            flash(f'O e-mail "{form.email.data}" já está cadastrado.', 'danger')
        else:
            driver.full_name = form.full_name.data
            driver.username = form.username.data
            driver.email = form.email.data
            driver.is_active = form.is_active.data
            if form.password.data:
                driver.set_password(form.password.data)
            db.session.commit()
            flash(f'Dados de "{driver.full_name}" atualizados.', 'success')
            return redirect(url_for('coordinator.drivers'))

    return render_template('coordinator/driver_form.html',
                           title='Editar Motorista', form=form, user=driver)


# ── Reservas para motoristas ──────────────────────────────────────────────────

@bp.route('/reservas-motorista')
@login_required
@role_required(Role.COORDINATOR)
def driver_reservations():
    reservations = DriverReservation.query.filter_by(
        coordinator_id=current_user.id
    ).order_by(DriverReservation.departure_datetime.desc()).all()
    return render_template('coordinator/driver_reservations.html',
                           title='Reservas para Motoristas',
                           reservations=reservations)


@bp.route('/reservas-motorista/nova', methods=['GET', 'POST'])
@login_required
@role_required(Role.COORDINATOR)
def new_driver_reservation():
    form = DriverReservationForm()

    all_drivers = User.query.filter_by(role=Role.DRIVER).all()
    my_drivers = [d for d in all_drivers if current_user in d.coordinators]
    form.driver_id.choices = [(d.id, d.full_name) for d in my_drivers]

    unavailable = get_unavailable_vehicle_ids()
    vehicles = Vehicle.query.filter_by(is_active=True).order_by(Vehicle.name).all()
    form.vehicle_id.choices = [
        (v.id, f'{v.name} — {v.plate} ({v.model})'
               + (' ⚠ INDISPONÍVEL' if v.id in unavailable else ''))
        for v in vehicles
    ]

    if form.validate_on_submit():
        if form.vehicle_id.data in unavailable:
            v = Vehicle.query.get(form.vehicle_id.data)
            flash(f'O veículo "{v.name}" está indisponível. Escolha outro.', 'danger')
        elif form.expected_return_datetime.data <= form.departure_datetime.data:
            flash('O retorno deve ser posterior à saída.', 'danger')
        else:
            reservation = DriverReservation(
                coordinator_id=current_user.id,
                driver_id=form.driver_id.data,
                vehicle_id=form.vehicle_id.data,
                departure_datetime=form.departure_datetime.data,
                expected_return_datetime=form.expected_return_datetime.data,
                reason=form.reason.data,
            )
            db.session.add(reservation)
            db.session.commit()
            flash('Reserva criada e aprovada automaticamente.', 'success')
            return redirect(url_for('coordinator.driver_reservations'))

    return render_template('coordinator/new_driver_reservation.html',
                           title='Nova Reserva para Motorista',
                           form=form, vehicles=vehicles, unavailable=unavailable)
