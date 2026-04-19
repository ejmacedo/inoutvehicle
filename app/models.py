from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, login_manager


class Role:
    ADMIN = 'admin'
    COORDINATOR = 'coordinator'
    EMPLOYEE = 'employee'
    SECURITY = 'security'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(140), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.EMPLOYEE)
    coordinator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    coordinator = db.relationship('User', remote_side=[id], backref='subordinates')
    requests = db.relationship('VehicleRequest', foreign_keys='VehicleRequest.employee_id',
                               backref='employee', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == Role.ADMIN

    def is_coordinator(self):
        return self.role == Role.COORDINATOR

    def is_employee(self):
        return self.role == Role.EMPLOYEE

    def is_security(self):
        return self.role == Role.SECURITY

    def __repr__(self):
        return f'<User {self.username}>'


class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    plate = db.Column(db.String(20), unique=True, nullable=False)
    model = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    requests = db.relationship('VehicleRequest', backref='vehicle', lazy='dynamic')

    def __repr__(self):
        return f'<Vehicle {self.plate}>'


class RequestStatus:
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'


class VehicleRequest(db.Model):
    __tablename__ = 'vehicle_requests'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    departure_datetime = db.Column(db.DateTime, nullable=False)
    expected_return_datetime = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    returns_to_company = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(db.String(20), nullable=False, default=RequestStatus.PENDING)
    coordinator_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def is_pending(self):
        return self.status == RequestStatus.PENDING

    def is_approved(self):
        return self.status == RequestStatus.APPROVED

    def is_rejected(self):
        return self.status == RequestStatus.REJECTED

    def __repr__(self):
        return f'<VehicleRequest {self.id} - {self.status}>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
