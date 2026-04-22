from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, login_manager


class Role:
    ADMIN = 'admin'
    COORDINATOR = 'coordinator'
    EMPLOYEE = 'employee'
    SECURITY = 'security'
    DRIVER = 'driver'


employee_coordinators = db.Table(
    'employee_coordinators',
    db.Column('employee_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('coordinator_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(140), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.EMPLOYEE)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    coordinators = db.relationship(
        'User',
        secondary=employee_coordinators,
        primaryjoin='User.id == employee_coordinators.c.employee_id',
        secondaryjoin='User.id == employee_coordinators.c.coordinator_id',
        backref=db.backref('employees', lazy='select'),
        lazy='select',
    )

    requests = db.relationship(
        'VehicleRequest',
        foreign_keys='VehicleRequest.employee_id',
        backref='employee',
        lazy='dynamic',
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):       return self.role == Role.ADMIN
    def is_coordinator(self): return self.role == Role.COORDINATOR
    def is_employee(self):    return self.role == Role.EMPLOYEE
    def is_security(self):    return self.role == Role.SECURITY
    def is_driver(self):      return self.role == Role.DRIVER

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
    driver_reservations = db.relationship('DriverReservation', backref='vehicle', lazy='dynamic')

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

    actual_departure_datetime = db.Column(db.DateTime, nullable=True)
    actual_return_datetime = db.Column(db.DateTime, nullable=True)

    odometer_departure = db.Column(db.Integer, nullable=True)
    odometer_return = db.Column(db.Integer, nullable=True)

    reason = db.Column(db.Text, nullable=False)
    returns_to_company = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(db.String(20), nullable=False, default=RequestStatus.PENDING)
    coordinator_notes = db.Column(db.Text, nullable=True)
    portaria_obs = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def is_pending(self):  return self.status == RequestStatus.PENDING
    def is_approved(self): return self.status == RequestStatus.APPROVED
    def is_rejected(self): return self.status == RequestStatus.REJECTED

    def __repr__(self):
        return f'<VehicleRequest {self.id} - {self.status}>'


class DriverReservation(db.Model):
    """Reserva criada diretamente pelo coordenador para um motorista. Auto-aprovada."""
    __tablename__ = 'driver_reservations'

    id = db.Column(db.Integer, primary_key=True)
    coordinator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)

    departure_datetime = db.Column(db.DateTime, nullable=False)
    expected_return_datetime = db.Column(db.DateTime, nullable=False)

    actual_departure_datetime = db.Column(db.DateTime, nullable=True)
    actual_return_datetime = db.Column(db.DateTime, nullable=True)

    odometer_departure = db.Column(db.Integer, nullable=True)
    odometer_return = db.Column(db.Integer, nullable=True)

    reason = db.Column(db.Text, nullable=False)
    portaria_obs = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    coordinator = db.relationship('User', foreign_keys=[coordinator_id],
                                  backref='reservations_created')
    driver = db.relationship('User', foreign_keys=[driver_id],
                             backref='driver_reservations')

    def __repr__(self):
        return f'<DriverReservation {self.id}>'


class AuditLog(db.Model):
    """Registro imutável de todas as ações relevantes do sistema."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(64), nullable=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = db.relationship('User', foreign_keys=[user_id], backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} by {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
