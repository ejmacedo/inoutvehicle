from wtforms.validators import ValidationError


def strong_password(form, field):
    """Requer mínimo 8 chars, maiúscula, minúscula e dígito."""
    pw = field.data
    if not pw:
        return
    errors = []
    if len(pw) < 8:
        errors.append('mínimo 8 caracteres')
    if not any(c.isupper() for c in pw):
        errors.append('uma letra maiúscula')
    if not any(c.islower() for c in pw):
        errors.append('uma letra minúscula')
    if not any(c.isdigit() for c in pw):
        errors.append('um número')
    if errors:
        raise ValidationError(f'A senha deve conter: {", ".join(errors)}.')
