"""Fixtures compartilhadas por toda a suíte de testes."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.pool import StaticPool
from app import create_app
from app.extensions import db as _db
from app.models import User, Vehicle, VehicleRequest, DriverReservation, RequestStatus, Role


class TestConfig:
    TESTING = True
    # StaticPool garante que todos os contextos compartilhem a mesma conexão
    # in-memory, eliminando o problema de "DBs diferentes por contexto"
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False},
        'poolclass': StaticPool,
    }
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    MAIL_SERVER = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SERVER_NAME = 'localhost'


# ── App / DB ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope='session')
def app():
    application = create_app(TestConfig)
    return application


@pytest.fixture
def client(app):
    """Cliente HTTP com banco zerado a cada teste."""
    with app.app_context():
        _db.create_all()
        yield app.test_client()
        _db.session.remove()
        _db.drop_all()


# ── Helpers ───────────────────────────────────────────────────────────────────

def login(client, username, password='Senha123'):
    return client.post('/login', data={'username': username, 'password': password},
                       follow_redirects=True)


def logout(client):
    return client.get('/logout', follow_redirects=True)


def make_dt(offset_hours=2):
    """Retorna datetime.now() + offset como string para DateTimeLocalField."""
    dt = datetime.now() + timedelta(hours=offset_hours)
    return dt.strftime('%Y-%m-%dT%H:%M')


# ── Factories de usuários ─────────────────────────────────────────────────────

def _user(username, role, password='Senha123', active=True):
    full_name = username.replace('_', ' ').replace('.', ' ').title()
    u = User(username=username, email=f'{username}@test.com',
             full_name=full_name, role=role, is_active=active)
    u.set_password(password)
    return u


@pytest.fixture
def admin(client, app):
    with app.app_context():
        u = _user('admin_user', Role.ADMIN)
        _db.session.add(u)
        _db.session.commit()
        return u.id


@pytest.fixture
def coordinator(client, app):
    with app.app_context():
        u = _user('coord_user', Role.COORDINATOR)
        _db.session.add(u)
        _db.session.commit()
        return u.id


@pytest.fixture
def coordinator2(client, app):
    with app.app_context():
        u = _user('coord2_user', Role.COORDINATOR)
        _db.session.add(u)
        _db.session.commit()
        return u.id


@pytest.fixture
def employee(client, app, coordinator):
    with app.app_context():
        e = _user('emp_user', Role.EMPLOYEE)
        coord = _db.session.get(User, coordinator)
        e.coordinators.append(coord)
        _db.session.add(e)
        _db.session.commit()
        return e.id


@pytest.fixture
def employee2(client, app, coordinator):
    with app.app_context():
        e = _user('emp2_user', Role.EMPLOYEE)
        coord = _db.session.get(User, coordinator)
        e.coordinators.append(coord)
        _db.session.add(e)
        _db.session.commit()
        return e.id


@pytest.fixture
def driver(client, app, coordinator):
    with app.app_context():
        d = _user('driver_user', Role.DRIVER)
        coord = _db.session.get(User, coordinator)
        d.coordinators.append(coord)
        _db.session.add(d)
        _db.session.commit()
        return d.id


@pytest.fixture
def security_user(client, app):
    with app.app_context():
        u = _user('security_user', Role.SECURITY)
        _db.session.add(u)
        _db.session.commit()
        return u.id


@pytest.fixture
def inactive_user(client, app):
    with app.app_context():
        u = _user('inactive_user', Role.EMPLOYEE, active=False)
        _db.session.add(u)
        _db.session.commit()
        return u.id


# ── Veículos ──────────────────────────────────────────────────────────────────

@pytest.fixture
def vehicle(client, app):
    with app.app_context():
        v = Vehicle(name='Gol Prata', plate='TST-0001', model='Volkswagen Gol', is_active=True)
        _db.session.add(v)
        _db.session.commit()
        return v.id


@pytest.fixture
def vehicle2(client, app):
    with app.app_context():
        v = Vehicle(name='Uno Branco', plate='TST-0002', model='Fiat Uno', is_active=True)
        _db.session.add(v)
        _db.session.commit()
        return v.id


# ── VehicleRequests ───────────────────────────────────────────────────────────

@pytest.fixture
def pending_request(client, app, employee, vehicle):
    with app.app_context():
        vr = VehicleRequest(
            employee_id=employee,
            vehicle_id=vehicle,
            departure_datetime=datetime.now() + timedelta(hours=1),
            expected_return_datetime=datetime.now() + timedelta(hours=5),
            reason='Visita ao cliente para apresentação de proposta.',
            returns_to_company=True,
            status=RequestStatus.PENDING,
        )
        _db.session.add(vr)
        _db.session.commit()
        return vr.id


@pytest.fixture
def approved_request(client, app, employee, vehicle):
    with app.app_context():
        vr = VehicleRequest(
            employee_id=employee,
            vehicle_id=vehicle,
            departure_datetime=datetime.now() + timedelta(hours=1),
            expected_return_datetime=datetime.now() + timedelta(hours=5),
            reason='Entrega de materiais no depósito central.',
            returns_to_company=True,
            status=RequestStatus.APPROVED,
        )
        _db.session.add(vr)
        _db.session.commit()
        return vr.id


@pytest.fixture
def departed_request(client, app, employee, vehicle):
    """Solicitação aprovada com saída já registrada pela portaria."""
    with app.app_context():
        vr = VehicleRequest(
            employee_id=employee,
            vehicle_id=vehicle,
            departure_datetime=datetime.now() - timedelta(hours=1),
            expected_return_datetime=datetime.now() + timedelta(hours=3),
            reason='Reunião com fornecedores.',
            returns_to_company=True,
            status=RequestStatus.APPROVED,
            actual_departure_datetime=datetime.now() - timedelta(minutes=30),
            odometer_departure=50000,
        )
        _db.session.add(vr)
        _db.session.commit()
        return vr.id


@pytest.fixture
def driver_reservation(client, app, coordinator, driver, vehicle):
    with app.app_context():
        dr = DriverReservation(
            coordinator_id=coordinator,
            driver_id=driver,
            vehicle_id=vehicle,
            departure_datetime=datetime.now() + timedelta(hours=1),
            expected_return_datetime=datetime.now() + timedelta(hours=6),
            reason='Transporte de equipamentos.',
        )
        _db.session.add(dr)
        _db.session.commit()
        return dr.id
