from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.admin import bp
from app.admin.forms import UserForm, EditUserForm, VehicleForm
from app.models import User, Vehicle, VehicleRequest, Role
from app.extensions import db
from app.decorators import role_required


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
    coordinators = User.query.filter_by(role=Role.COORDINATOR, is_active=True).order_by(User.full_name).all()
    form.coordinator_id.choices = [(0, '-- Nenhum --')] + [(c.id, c.full_name) for c in coordinators]

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data,
            is_active=form.is_active.data,
            coordinator_id=form.coordinator_id.data if form.coordinator_id.data != 0 else None,
        )
        user.set_password(form.password.data)
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
    coordinators = User.query.filter_by(role=Role.COORDINATOR, is_active=True).order_by(User.full_name).all()
    form.coordinator_id.choices = [(0, '-- Nenhum --')] + [(c.id, c.full_name) for c in coordinators]

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        user.coordinator_id = form.coordinator_id.data if form.coordinator_id.data != 0 else None
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash(f'Usuário {user.username} atualizado com sucesso.', 'success')
        return redirect(url_for('admin.users'))

    form.coordinator_id.data = user.coordinator_id or 0
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
