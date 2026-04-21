"""Testes da portaria: saída e retorno de funcionários e motoristas."""
from datetime import datetime, timedelta
from tests.conftest import login
from app.models import VehicleRequest, DriverReservation
from app.extensions import db


class TestPortariaDashboard:
    def test_dashboard_carrega(self, client, security_user):
        login(client, 'security_user')
        r = client.get('/portaria/dashboard')
        assert r.status_code == 200
        assert b'Portaria' in r.data

    def test_funcionario_nao_acessa_portaria(self, client, employee):
        login(client, 'emp_user')
        r = client.get('/portaria/dashboard', follow_redirects=True)
        assert r.status_code == 403

    def test_dashboard_exibe_solicitacao_aprovada(self, client, security_user, approved_request):
        login(client, 'security_user')
        r = client.get('/portaria/dashboard')
        assert b'SAIU' in r.data

    def test_filtro_por_nome(self, client, security_user, approved_request):
        login(client, 'security_user')
        r = client.get('/portaria/dashboard?name=emp')
        assert r.status_code == 200
        assert b'Emp' in r.data

    def test_filtro_por_veiculo(self, client, security_user, approved_request, vehicle):
        login(client, 'security_user')
        r = client.get(f'/portaria/dashboard?vehicle_id={vehicle}')
        assert r.status_code == 200

    def test_filtro_por_data(self, client, security_user, approved_request):
        today = datetime.now().strftime('%Y-%m-%d')
        login(client, 'security_user')
        r = client.get(f'/portaria/dashboard?date={today}')
        assert r.status_code == 200

    def test_filtro_nome_sem_resultado(self, client, security_user, approved_request):
        login(client, 'security_user')
        r = client.get('/portaria/dashboard?name=XYZInexistente')
        assert r.status_code == 200
        assert b'SAIU' not in r.data


class TestSaidaFuncionario:
    def test_registrar_saida_com_km(self, client, app, security_user, approved_request):
        login(client, 'security_user')
        r = client.post(f'/portaria/solicitacao/{approved_request}/saiu',
                        data={'odometer': '45000'}, follow_redirects=True)
        assert r.status_code == 200
        assert b'registrada' in r.data.lower()
        with app.app_context():
            vr = db.session.get(VehicleRequest, approved_request)
            assert vr.actual_departure_datetime is not None
            assert vr.odometer_departure == 45000

    def test_registrar_saida_sem_km_falha(self, client, security_user, approved_request):
        login(client, 'security_user')
        r = client.post(f'/portaria/solicitacao/{approved_request}/saiu',
                        data={'odometer': ''}, follow_redirects=True)
        assert b'quilometragem' in r.data.lower()
        # Saída NÃO deve ser registrada

    def test_registrar_saida_km_zero_falha(self, client, security_user, approved_request):
        login(client, 'security_user')
        r = client.post(f'/portaria/solicitacao/{approved_request}/saiu',
                        data={'odometer': '0'}, follow_redirects=True)
        assert b'quilometragem' in r.data.lower()

    def test_registrar_saida_km_negativo_falha(self, client, security_user, approved_request):
        login(client, 'security_user')
        r = client.post(f'/portaria/solicitacao/{approved_request}/saiu',
                        data={'odometer': '-100'}, follow_redirects=True)
        assert b'quilometragem' in r.data.lower()


class TestRetornoFuncionario:
    def test_registrar_retorno_com_km(self, client, app, security_user, departed_request):
        login(client, 'security_user')
        r = client.post(f'/portaria/solicitacao/{departed_request}/voltou',
                        data={'odometer': '50250'}, follow_redirects=True)
        assert r.status_code == 200
        assert b'registrado' in r.data.lower()
        with app.app_context():
            vr = db.session.get(VehicleRequest, departed_request)
            assert vr.actual_return_datetime is not None
            assert vr.odometer_return == 50250

    def test_registrar_retorno_sem_km_falha(self, client, security_user, departed_request):
        login(client, 'security_user')
        r = client.post(f'/portaria/solicitacao/{departed_request}/voltou',
                        data={'odometer': ''}, follow_redirects=True)
        assert b'quilometragem' in r.data.lower()

    def test_retorno_sem_saida_previa_falha(self, client, security_user, approved_request):
        """Tenta registrar retorno sem ter registrado saída primeiro."""
        login(client, 'security_user')
        r = client.post(f'/portaria/solicitacao/{approved_request}/voltou',
                        data={'odometer': '50000'}, follow_redirects=True)
        assert b'sa' in r.data.lower()   # "registre a saída antes"


class TestSaidaMotorista:
    def test_registrar_saida_motorista_com_km(self, client, app, security_user,
                                               driver_reservation):
        login(client, 'security_user')
        r = client.post(f'/portaria/reserva/{driver_reservation}/saiu',
                        data={'odometer': '30000'}, follow_redirects=True)
        assert r.status_code == 200
        assert b'registrada' in r.data.lower()
        with app.app_context():
            dr = db.session.get(DriverReservation, driver_reservation)
            assert dr.actual_departure_datetime is not None
            assert dr.odometer_departure == 30000

    def test_registrar_saida_motorista_sem_km_falha(self, client, security_user,
                                                     driver_reservation):
        login(client, 'security_user')
        r = client.post(f'/portaria/reserva/{driver_reservation}/saiu',
                        data={'odometer': ''}, follow_redirects=True)
        assert b'quilometragem' in r.data.lower()


class TestRetornoMotorista:
    def test_registrar_retorno_motorista_com_km(self, client, app, security_user,
                                                 driver_reservation):
        """Registra saída e depois retorno do motorista."""
        login(client, 'security_user')
        # Primeiro registra a saída
        client.post(f'/portaria/reserva/{driver_reservation}/saiu',
                    data={'odometer': '30000'})
        # Depois registra o retorno
        r = client.post(f'/portaria/reserva/{driver_reservation}/voltou',
                        data={'odometer': '30500'}, follow_redirects=True)
        assert r.status_code == 200
        assert b'registrado' in r.data.lower()
        with app.app_context():
            dr = db.session.get(DriverReservation, driver_reservation)
            assert dr.actual_return_datetime is not None
            assert dr.odometer_return == 30500

    def test_retorno_motorista_sem_km_falha(self, client, app, security_user,
                                             driver_reservation):
        login(client, 'security_user')
        # Registra saída primeiro
        client.post(f'/portaria/reserva/{driver_reservation}/saiu',
                    data={'odometer': '30000'})
        r = client.post(f'/portaria/reserva/{driver_reservation}/voltou',
                        data={'odometer': ''}, follow_redirects=True)
        assert b'quilometragem' in r.data.lower()

    def test_retorno_motorista_sem_saida_falha(self, client, security_user,
                                               driver_reservation):
        login(client, 'security_user')
        r = client.post(f'/portaria/reserva/{driver_reservation}/voltou',
                        data={'odometer': '30500'}, follow_redirects=True)
        assert b'sa' in r.data.lower()


class TestObsPortaria:
    def test_obs_gerada_para_atraso_30min(self, client, app, security_user, coordinator,
                                          employee, vehicle):
        """Saída 35 minutos após o horário previsto deve gerar OBS portaria."""
        with app.app_context():
            from app.models import VehicleRequest as VR, RequestStatus as RS
            vr = VR(
                employee_id=employee,
                vehicle_id=vehicle,
                departure_datetime=datetime.now() - timedelta(minutes=35),
                expected_return_datetime=datetime.now() + timedelta(hours=4),
                reason='Entrega urgente de documentos para escritório parceiro.',
                returns_to_company=True,
                status=RS.APPROVED,
            )
            db.session.add(vr)
            db.session.commit()
            vr_id = vr.id

        login(client, 'security_user')
        client.post(f'/portaria/solicitacao/{vr_id}/saiu', data={'odometer': '10000'})

        with app.app_context():
            vr = db.session.get(VehicleRequest, vr_id)
            assert vr.portaria_obs is not None
            assert 'depois' in vr.portaria_obs

    def test_sem_obs_para_diferenca_menor_30min(self, client, app, security_user,
                                                 coordinator, employee, vehicle):
        """Diferença de 10 minutos não deve gerar OBS."""
        with app.app_context():
            from app.models import VehicleRequest as VR, RequestStatus as RS
            vr = VR(
                employee_id=employee,
                vehicle_id=vehicle,
                departure_datetime=datetime.now() - timedelta(minutes=10),
                expected_return_datetime=datetime.now() + timedelta(hours=4),
                reason='Reunião de alinhamento com cliente estratégico.',
                returns_to_company=True,
                status=RS.APPROVED,
            )
            db.session.add(vr)
            db.session.commit()
            vr_id = vr.id

        login(client, 'security_user')
        client.post(f'/portaria/solicitacao/{vr_id}/saiu', data={'odometer': '10000'})

        with app.app_context():
            vr = db.session.get(VehicleRequest, vr_id)
            assert vr.portaria_obs is None
