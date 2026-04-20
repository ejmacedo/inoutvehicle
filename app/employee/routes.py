from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.employee import bp
from app.employee.forms import VehicleRequestForm
from app.models import Vehicle, VehicleRequest, RequestStatus, Role
from app.extensions import db
from app.decorators import role_required
from app.email_utils import notify_coordinators_new_request


@bp.route('/dashboard')
@login_required
@role_required(Role.EMPLOYEE)
def dashboard():
    requests = VehicleRequest.query.filter_by(employee_id=current_user.id)\
        .order_by(VehicleRequest.created_at.desc()).all()
    return render_template('employee/dashboard.html', title='Minhas Solicitações', requests=requests)


@bp.route('/solicitar', methods=['GET', 'POST'])
@login_required
@role_required(Role.EMPLOYEE)
def new_request():
    form = VehicleRequestForm()
    vehicles = Vehicle.query.filter_by(is_active=True).all()
    form.vehicle_id.choices = [(v.id, f'{v.name} — {v.plate} ({v.model})') for v in vehicles]

    if form.validate_on_submit():
        departure = form.departure_datetime.data
        expected_return = form.expected_return_datetime.data

        if expected_return <= departure:
            flash('A previsão de chegada deve ser posterior à data de saída.', 'danger')
            return render_template('employee/new_request.html', title='Solicitar Veículo', form=form)

        conflict = VehicleRequest.query.filter(
            VehicleRequest.vehicle_id == form.vehicle_id.data,
            VehicleRequest.status == RequestStatus.APPROVED,
            VehicleRequest.departure_datetime < expected_return,
            VehicleRequest.expected_return_datetime > departure,
        ).first()

        if conflict:
            flash(
                f'O veículo selecionado não está disponível neste período. '
                f'Já existe uma reserva aprovada de '
                f'{conflict.departure_datetime.strftime("%d/%m/%Y %H:%M")} até '
                f'{conflict.expected_return_datetime.strftime("%d/%m/%Y %H:%M")}.',
                'danger',
            )
            return render_template('employee/new_request.html', title='Solicitar Veículo', form=form)

        vehicle_request = VehicleRequest(
            employee_id=current_user.id,
            vehicle_id=form.vehicle_id.data,
            departure_datetime=departure,
            expected_return_datetime=expected_return,
            reason=form.reason.data,
            returns_to_company=form.returns_to_company.data,
            status=RequestStatus.PENDING,
        )
        db.session.add(vehicle_request)
        db.session.commit()
        notify_coordinators_new_request(vehicle_request)
        flash('Solicitação enviada! Aguardando aprovação do coordenador.', 'success')
        return redirect(url_for('employee.dashboard'))

    form.full_name.data = current_user.full_name
    return render_template('employee/new_request.html', title='Solicitar Veículo', form=form)
