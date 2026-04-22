from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.admin import bp
from app.admin.forms import UserForm, EditUserForm, VehicleForm
from app.models import User, Vehicle, VehicleRequest, AuditLog, Role
from app.extensions import db
from app.decorators import role_required
from app.audit import log_action


def _coordinator_choices():
    coordinators = (User.query
                    .filter_by(role=Role.COORDINATOR, is_active=True)
                    .order_by(User.full_name).all())
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
        if User.query.filter_by(username=form.username.data).first():
            flash(f'O nome de usuário "{form.username.data}" já está em uso. Escolha outro.', 'danger')
            return render_template('admin/user_form.html', title='Novo Usuário', form=form)

        if User.query.filter_by(email=form.email.data).first():
            flash(f'O e-mail "{form.email.data}" já está cadastrado. Use outro endereço.', 'danger')
            return render_template('admin/user_form.html', title='Novo Usuário', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data,
            is_active=form.is_active.data,
        )
        user.set_password(form.password.data)
        if form.role.data == Role.EMPLOYEE and form.coordinator_ids.data:
            coords = User.query.filter(User.id.in_(form.coordinator_ids.data)).all()
            user.coordinators = coords
        db.session.add(user)
        db.session.commit()
        log_action('USUARIO_CRIADO',
                   f'Usuário "{user.username}" (perfil: {user.role}) criado pelo admin')
        flash(f'Usuário "{user.username}" criado com sucesso.', 'success')
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
        if (form.username.data != user.username and
                User.query.filter_by(username=form.username.data).first()):
            flash(f'O nome de usuário "{form.username.data}" já está em uso. Escolha outro.', 'danger')
            form.coordinator_ids.data = [c.id for c in user.coordinators]
            return render_template('admin/user_form.html', title='Editar Usuário', form=form, user=user)

        if (form.email.data != user.email and
                User.query.filter_by(email=form.email.data).first()):
            flash(f'O e-mail "{form.email.data}" já está cadastrado. Use outro endereço.', 'danger')
            form.coordinator_ids.data = [c.id for c in user.coordinators]
            return render_template('admin/user_form.html', title='Editar Usuário', form=form, user=user)

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
        log_action('USUARIO_ATUALIZADO',
                   f'Usuário "{user.username}" (ID {user.id}) atualizado pelo admin')
        flash(f'Usuário "{user.username}" atualizado com sucesso.', 'success')
        return redirect(url_for('admin.users'))

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
        plate_upper = form.plate.data.upper()
        if Vehicle.query.filter_by(plate=plate_upper).first():
            flash(f'Já existe um veículo cadastrado com a placa "{plate_upper}".', 'danger')
            return render_template('admin/vehicle_form.html', title='Novo Veículo', form=form)

        vehicle = Vehicle(
            name=form.name.data,
            plate=plate_upper,
            model=form.model.data,
            is_active=form.is_active.data,
        )
        db.session.add(vehicle)
        db.session.commit()
        log_action('VEICULO_CRIADO',
                   f'Veículo "{vehicle.name}" (placa: {vehicle.plate}) cadastrado')
        flash(f'Veículo "{vehicle.name}" cadastrado com sucesso.', 'success')
        return redirect(url_for('admin.vehicles'))
    return render_template('admin/vehicle_form.html', title='Novo Veículo', form=form)


@bp.route('/veiculos/<int:vehicle_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(Role.ADMIN)
def edit_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    form = VehicleForm(obj=vehicle)
    if form.validate_on_submit():
        plate_upper = form.plate.data.upper()
        existing = Vehicle.query.filter_by(plate=plate_upper).first()
        if existing and existing.id != vehicle.id:
            flash(f'Já existe outro veículo cadastrado com a placa "{plate_upper}".', 'danger')
            return render_template('admin/vehicle_form.html', title='Editar Veículo', form=form, vehicle=vehicle)

        vehicle.name = form.name.data
        vehicle.plate = plate_upper
        vehicle.model = form.model.data
        vehicle.is_active = form.is_active.data
        db.session.commit()
        log_action('VEICULO_ATUALIZADO',
                   f'Veículo "{vehicle.name}" (placa: {vehicle.plate}) atualizado')
        flash(f'Veículo "{vehicle.name}" atualizado com sucesso.', 'success')
        return redirect(url_for('admin.vehicles'))
    return render_template('admin/vehicle_form.html', title='Editar Veículo', form=form, vehicle=vehicle)


# ── Log de Auditoria ──────────────────────────────────────────────────────────

@bp.route('/auditoria')
@login_required
@role_required(Role.ADMIN)
def audit_log():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()
    user_filter = request.args.get('user', '').strip()

    query = AuditLog.query.order_by(AuditLog.created_at.desc())

    if action_filter:
        query = query.filter(AuditLog.action.ilike(f'%{action_filter}%'))
    if user_filter:
        query = query.filter(AuditLog.username.ilike(f'%{user_filter}%'))

    logs = query.paginate(page=page, per_page=50, error_out=False)

    # Ações distintas para o filtro dropdown
    actions = [r[0] for r in db.session.query(AuditLog.action).distinct().order_by(AuditLog.action).all()]

    return render_template('admin/audit_log.html',
                           title='Log de Auditoria',
                           logs=logs,
                           actions=actions,
                           action_filter=action_filter,
                           user_filter=user_filter)
