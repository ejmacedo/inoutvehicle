"""Testes do painel de coordenador: aprovação, recusa, funcionários, motoristas e reservas."""
from tests.conftest import login, make_dt
from app.models import VehicleRequest, DriverReservation, User, RequestStatus
from app.extensions import db


class TestCoordinatorDashboard:
    def test_dashboard_carrega(self, client, coordinator):
        login(client, 'coord_user')
        r = client.get('/coordenador/dashboard')
        assert r.status_code == 200
        assert b'Painel do Coordenador' in r.data

    def test_dashboard_exibe_pendentes(self, client, coordinator, pending_request):
        login(client, 'coord_user')
        r = client.get('/coordenador/dashboard')
        assert b'Pendente' in r.data or b'pendente' in r.data.lower()

    def test_funcionario_nao_acessa_coordenador(self, client, employee):
        login(client, 'emp_user')
        r = client.get('/coordenador/dashboard', follow_redirects=True)
        assert r.status_code == 403


class TestAprovar:
    def test_aprovar_solicitacao(self, client, app, coordinator, pending_request, vehicle):
        login(client, 'coord_user')
        r = client.post(f'/coordenador/solicitacao/{pending_request}/aprovar', data={
            'vehicle_id': vehicle,
            'notes': 'Aprovado sem observações.',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'aprovada' in r.data.lower()
        with app.app_context():
            vr = db.session.get(VehicleRequest, pending_request)
            assert vr.status == RequestStatus.APPROVED

    def test_aprovar_com_troca_de_veiculo(self, client, app, coordinator,
                                           pending_request, vehicle, vehicle2):
        login(client, 'coord_user')
        r = client.post(f'/coordenador/solicitacao/{pending_request}/aprovar', data={
            'vehicle_id': vehicle2,   # veículo diferente do original
            'notes': '',
        }, follow_redirects=True)
        assert r.status_code == 200
        with app.app_context():
            vr = db.session.get(VehicleRequest, pending_request)
            assert vr.vehicle_id == vehicle2
            assert 'alterado' in (vr.coordinator_notes or '').lower()

    def test_aprovar_sem_veiculo_falha(self, client, coordinator, pending_request):
        login(client, 'coord_user')
        r = client.post(f'/coordenador/solicitacao/{pending_request}/aprovar', data={
            'notes': 'Sem veículo selecionado.',
        }, follow_redirects=True)
        assert b'Selecione' in r.data or b'selecione' in r.data.lower()

    def test_aprovar_veiculo_indisponivel_bloqueado(self, client, app, coordinator,
                                                     pending_request, vehicle, vehicle2):
        """Tenta aprovar com veículo que já está em uso."""
        with app.app_context():
            from app.models import VehicleRequest as VR, RequestStatus as RS
            vr_block = VR(
                employee_id=pending_request,   # só precisa de um employee_id qualquer
                vehicle_id=vehicle2,
                departure_datetime=__import__('datetime').datetime.now(),
                expected_return_datetime=__import__('datetime').datetime.now()
                    + __import__('datetime').timedelta(hours=5),
                reason='Bloqueio de teste.',
                returns_to_company=True,
                status=RS.APPROVED,
            )
            # Busca um employee real
            from app.models import User, Role
            emp = User.query.filter_by(role=Role.EMPLOYEE).first()
            vr_block.employee_id = emp.id
            db.session.add(vr_block)
            db.session.commit()

        login(client, 'coord_user')
        r = client.post(f'/coordenador/solicitacao/{pending_request}/aprovar', data={
            'vehicle_id': vehicle2,
            'notes': '',
        }, follow_redirects=True)
        assert b'indispon' in r.data.lower()

    def test_coordenador_nao_aprova_de_outro_coordenador(self, client, app,
                                                          coordinator2, pending_request, vehicle):
        """Coordenador 2 não pode aprovar solicitação de funcionário do coordenador 1."""
        login(client, 'coord2_user')
        r = client.post(f'/coordenador/solicitacao/{pending_request}/aprovar', data={
            'vehicle_id': vehicle,
            'notes': '',
        }, follow_redirects=True)
        assert r.status_code == 403


class TestRecusar:
    def test_recusar_com_motivo(self, client, app, coordinator, pending_request, vehicle):
        login(client, 'coord_user')
        r = client.post(f'/coordenador/solicitacao/{pending_request}/recusar', data={
            'notes': 'Veículo necessário para outra demanda urgente.',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'recusada' in r.data.lower()
        with app.app_context():
            vr = db.session.get(VehicleRequest, pending_request)
            assert vr.status == RequestStatus.REJECTED

    def test_recusar_sem_motivo_falha(self, client, coordinator, pending_request):
        login(client, 'coord_user')
        r = client.post(f'/coordenador/solicitacao/{pending_request}/recusar', data={
            'notes': '',
        }, follow_redirects=True)
        assert b'motivo' in r.data.lower()

    def test_coordenador_nao_recusa_de_outro_coordenador(self, client, coordinator2,
                                                          pending_request):
        login(client, 'coord2_user')
        r = client.post(f'/coordenador/solicitacao/{pending_request}/recusar', data={
            'notes': 'Tentativa indevida.',
        }, follow_redirects=True)
        assert r.status_code == 403


class TestFuncionarios:
    def test_lista_funcionarios(self, client, coordinator, employee):
        login(client, 'coord_user')
        r = client.get('/coordenador/funcionarios')
        assert r.status_code == 200
        assert b'Emp User' in r.data

    def test_editar_funcionario_get(self, client, coordinator, employee):
        login(client, 'coord_user')
        r = client.get(f'/coordenador/funcionarios/{employee}/editar')
        assert r.status_code == 200
        assert b'Editar Funcion' in r.data

    def test_editar_funcionario_post(self, client, app, coordinator, employee):
        login(client, 'coord_user')
        r = client.post(f'/coordenador/funcionarios/{employee}/editar', data={
            'full_name': 'Emp Atualizado',
            'username': 'emp_user',
            'email': 'emp_user@test.com',
            'password': '',
            'password2': '',
            'is_active': 'y',
        }, follow_redirects=True)
        assert r.status_code == 200
        with app.app_context():
            u = db.session.get(User, employee)
            assert u.full_name == 'Emp Atualizado'

    def test_coordenador_nao_edita_funcionario_de_outro(self, client, coordinator2, employee):
        login(client, 'coord2_user')
        r = client.get(f'/coordenador/funcionarios/{employee}/editar', follow_redirects=True)
        assert r.status_code == 403


class TestMotoristas:
    def test_lista_motoristas(self, client, coordinator, driver):
        login(client, 'coord_user')
        r = client.get('/coordenador/motoristas')
        assert r.status_code == 200
        assert b'Driver User' in r.data

    def test_criar_motorista(self, client, app, coordinator):
        login(client, 'coord_user')
        r = client.post('/coordenador/motoristas/novo', data={
            'full_name': 'Novo Motorista',
            'username': 'novo_driver',
            'email': 'novo_driver@test.com',
            'password': 'senha123',
            'password2': 'senha123',
            'is_active': 'y',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'cadastrado' in r.data.lower()
        with app.app_context():
            u = User.query.filter_by(username='novo_driver').first()
            assert u is not None
            assert u.role == 'driver'

    def test_criar_motorista_usuario_duplicado(self, client, coordinator, driver):
        login(client, 'coord_user')
        r = client.post('/coordenador/motoristas/novo', data={
            'full_name': 'Duplicado',
            'username': 'driver_user',   # já existe
            'email': 'outro@test.com',
            'password': 'senha123',
            'password2': 'senha123',
            'is_active': 'y',
        }, follow_redirects=True)
        assert b'j' in r.data.lower() and b'uso' in r.data.lower()

    def test_editar_motorista(self, client, app, coordinator, driver):
        login(client, 'coord_user')
        r = client.post(f'/coordenador/motoristas/{driver}/editar', data={
            'full_name': 'Driver Editado',
            'username': 'driver_user',
            'email': 'driver_user@test.com',
            'password': '',
            'password2': '',
            'is_active': 'y',
        }, follow_redirects=True)
        assert r.status_code == 200
        with app.app_context():
            u = db.session.get(User, driver)
            assert u.full_name == 'Driver Editado'


class TestReservasMotorista:
    def test_lista_reservas(self, client, coordinator, driver_reservation):
        login(client, 'coord_user')
        r = client.get('/coordenador/reservas-motorista')
        assert r.status_code == 200
        assert b'Reservas' in r.data

    def test_nova_reserva_valida(self, client, app, coordinator, driver, vehicle):
        login(client, 'coord_user')
        r = client.post('/coordenador/reservas-motorista/nova', data={
            'driver_id': driver,
            'vehicle_id': vehicle,
            'departure_datetime': make_dt(2),
            'expected_return_datetime': make_dt(8),
            'reason': 'Transporte de equipamentos para a filial.',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'criada' in r.data.lower()
        with app.app_context():
            dr = DriverReservation.query.filter_by(driver_id=driver).first()
            assert dr is not None

    def test_nova_reserva_retorno_antes_saida(self, client, coordinator, driver, vehicle):
        login(client, 'coord_user')
        r = client.post('/coordenador/reservas-motorista/nova', data={
            'driver_id': driver,
            'vehicle_id': vehicle,
            'departure_datetime': make_dt(8),
            'expected_return_datetime': make_dt(2),  # anterior
            'reason': 'Transporte de equipamentos para a filial.',
        }, follow_redirects=True)
        assert b'posterior' in r.data.lower()

    def test_nova_reserva_veiculo_indisponivel(self, client, app, coordinator,
                                               driver, vehicle, approved_request):
        login(client, 'coord_user')
        r = client.post('/coordenador/reservas-motorista/nova', data={
            'driver_id': driver,
            'vehicle_id': vehicle,   # está em approved_request sem retorno
            'departure_datetime': make_dt(2),
            'expected_return_datetime': make_dt(8),
            'reason': 'Transporte de equipamentos para a filial.',
        }, follow_redirects=True)
        assert b'indispon' in r.data.lower()
