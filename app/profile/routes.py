import json
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from app.profile import bp
from app.profile.forms import ChangePasswordForm
from app.models import Role, VehicleRequest
from app.extensions import db
from app.audit import log_action


@bp.route('/trocar-senha', methods=['GET', 'POST'])
@login_required
def change_password():
    if current_user.role == Role.SECURITY:
        flash('Portaria não tem permissão para alterar senha.', 'warning')
        return redirect(url_for('main.index'))

    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Senha atual incorreta.', 'danger')
            return render_template('profile/change_password.html',
                                   title='Trocar Senha', form=form)
        current_user.set_password(form.new_password.data)
        db.session.commit()
        log_action('SENHA_ALTERADA',
                   f"Usuário '{current_user.username}' alterou sua própria senha.")
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('main.index'))

    return render_template('profile/change_password.html', title='Trocar Senha', form=form)


@bp.route('/meus-dados')
@login_required
def my_data():
    requests = (VehicleRequest.query
                .filter_by(employee_id=current_user.id)
                .order_by(VehicleRequest.created_at.desc())
                .all())
    return render_template('profile/my_data.html', title='Meus Dados', requests=requests)


@bp.route('/exportar-dados')
@login_required
def export_data():
    requests = (VehicleRequest.query
                .filter_by(employee_id=current_user.id)
                .order_by(VehicleRequest.created_at.desc())
                .all())

    payload = {
        'exportado_em': datetime.now(timezone.utc).isoformat(),
        'titular': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'full_name': current_user.full_name,
            'role': current_user.role,
            'is_active': current_user.is_active,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
            'consent_accepted_at': (current_user.consent_accepted_at.isoformat()
                                    if current_user.consent_accepted_at else None),
        },
        'solicitacoes_de_veiculo': [
            {
                'id': r.id,
                'veiculo': r.vehicle.name,
                'placa': r.vehicle.plate,
                'saida_prevista': r.departure_datetime.isoformat(),
                'retorno_previsto': r.expected_return_datetime.isoformat(),
                'saida_real': r.actual_departure_datetime.isoformat() if r.actual_departure_datetime else None,
                'retorno_real': r.actual_return_datetime.isoformat() if r.actual_return_datetime else None,
                'odometro_saida': r.odometer_departure,
                'odometro_retorno': r.odometer_return,
                'motivo': r.reason,
                'status': r.status,
                'notas_coordenador': r.coordinator_notes,
                'criado_em': r.created_at.isoformat() if r.created_at else None,
            }
            for r in requests
        ],
    }

    log_action('DADOS_EXPORTADOS', f"Usuário '{current_user.username}' exportou seus dados pessoais.")
    filename = f'meus_dados_{current_user.username}.json'
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@bp.route('/solicitar-exclusao', methods=['POST'])
@login_required
def request_deletion():
    if current_user.deletion_requested_at:
        flash('Você já possui uma solicitação de exclusão pendente.', 'info')
        return redirect(url_for('profile.my_data'))

    current_user.deletion_requested_at = datetime.now(timezone.utc)
    db.session.commit()
    log_action('EXCLUSAO_SOLICITADA',
               f"Usuário '{current_user.username}' solicitou a exclusão dos seus dados (LGPD).")
    flash('Solicitação de exclusão registrada. O administrador irá processá-la em breve.', 'success')
    return redirect(url_for('profile.my_data'))
