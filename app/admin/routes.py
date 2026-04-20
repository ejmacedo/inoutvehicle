from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.admin import bp
from app.admin.forms import UserForm, EditUserForm, VehicleForm
from app.models import User, Vehicle, VehicleRequest, Role
from app.extensions import db
from app.decorators import role_required


def _coordinator_choices():
    coordinators = User.query.filter_by(role=Role.COORDINATOR, is_active=True).order_by(User.full_name).all()
    return [(c.id, c.full_name) for c in coordinators]


@bp.route('/dashboard')
@login_required
@role_required(Role.ADMIN)
def dashboard():
    total_users = User.query.count()
    total_vehicles = Vehicle.query.filter_by(is_active=True).count()
    total_requests = VehicleRequest.query.count()
    pending_requests = VehicleRequest.query.filter_by(status='pending').count()
    return render_template('admin/dashboard.html', title='Painel Admin',
                           total_users=total_users, total_vehicles=total_vehicles,
                           total_requests=total_requests, pending_requests=pending_requests)


@bp.route('/usuarios')
@login_required
@role_required(Role.ADMIN)
def users():
    all_users = User.query.order_by(User.full_name).all()
    return render_template('admin/users.html', title='Usuários', users=all_users)


@bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@role_required(Role.ADMIN)
def create_user():
    form = UserForm()
    form.coordinator_ids.choices = _coordinator_choices()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data,
            is_active=form.is_active.data,
        )
        user.set_password(form.password.data)
        # Atribui coordenadores selecionados
        if form.role.data == Role.EMPLOYEE and form.coordinator_ids.data:
            coords = User.query.filter(User.id.in_(form.coordinator_ids.data)).all()
            user.coordinators = coords
        db.session.add(user)
        db.session.commit()
        flash(f'Usuário {user.username} criado com sucesso.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', title='Novo Usuário', form=form)


@bp.route('/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(Role.ADMIN)
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(original_user=user, obj=user)
    form.coordinator_ids.choices = _coordinator_choices()

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        if form.password.data:
            user.set_password(form.password.data)
        if form.role.data == Role.EMPLOYEE:
            coords = User.query.filter(User.id.in_(form.coordinator_ids.data or [])).all()
            user.coordinators = coords
        else:
            user.coordinators = []
        db.session.commit()
        flash(f'Usuário {user.username} atualizado com sucesso.', 'success')
        return redirect(url_for('admin.users'))

    # Pré-seleciona coordenadores actuais
    form.coordinator_ids.data = [c.id for c in user.coordinators]
    return render_template('admin/user_form.html', title='Editar Usuário', form=form, user=user)


@bp.route('/veiculos')
@login_required
@role_required(Role.ADMIN)
def vehicles():
    all_vehicles = Vehicle.query.order_by(Vehicle.name).all()
    return render_template('admin/vehicles.html', title='Veículos', vehicles=all_vehicles)


@bp.route('/veiculos/novo', methods=['GET', 'POST'])
@login_required
@role_required(Role.ADMIN)
def create_vehicle():
    form = VehicleForm()
    if form.validate_on_submit():
        vehicle = Vehicle(
            name=form.name.data,
            plate=form.plate.data.upper(),
            model=form.model.data,
            is_active=form.is_active.data,
        )
        db.session.add(vehicle)
        db.session.commit()
        flash(f'Veículo {vehicle.name} cadastrado com sucesso.', 'success')
        return redirect(url_for('admin.vehicles'))
    return render_template('admin/vehicle_form.html', title='Novo Veículo', form=form)


@bp.route('/veiculos/<int:vehicle_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(Role.ADMIN)
def edit_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    form = VehicleForm(obj=vehicle)
    if form.validate_on_submit():
        vehicle.name = form.name.data
        vehicle.plate = form.plate.data.upper()
        vehicle.model = form.model.data
        vehicle.is_active = form.is_active.data
        db.session.commit()
        flash(f'Veículo {vehicle.name} atualizado com sucesso.', 'success')
        return redirect(url_for('admin.vehicles'))
    return render_template('admin/vehicle_form.html', title='Editar Veículo', form=form, vehicle=vehicle)
