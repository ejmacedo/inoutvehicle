"""Registro de auditoria — nunca interrompe o fluxo principal."""
from datetime import datetime, timezone
from flask import request
from flask_login import current_user


def log_action(action: str, description: str = None):
    try:
        from app.extensions import db
        from app.models import AuditLog
        entry = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            username=current_user.username if current_user.is_authenticated else None,
            action=action,
            description=description,
            ip_address=request.remote_addr,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        pass
