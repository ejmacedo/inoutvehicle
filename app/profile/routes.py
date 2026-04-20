from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.profile import bp
from app.profile.forms import ChangePasswordForm
from app.models import Role
from app.extensions import db


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
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('main.index'))

    return render_template('profile/change_password.html', title='Trocar Senha', form=form)
