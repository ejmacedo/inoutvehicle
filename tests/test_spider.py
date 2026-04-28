"""
Spider tests: acesso com perfil errado, IDs inexistentes, métodos incorretos,
parâmetros de URL manipulados. Simula um atacante tentando navegar pelo sistema.
"""
import pytest
from tests.conftest import login


# ── RBAC: perfil errado em cada área ─────────────────────────────────────────

class TestAcessoNegadoAdmin:
    """Nenhum perfil não-admin deve entrar em /admin/*."""

    @pytest.mark.parametrize('url', [
        '/admin/dashboard',
        '/admin/usuarios',
        '/admin/usuarios/novo',
        '/admin/veiculos',
        '/admin/veiculos/novo',
        '/admin/auditoria',
    ])
    def test_funcionario_bloqueado(self, client, employee, url):
        login(client, 'emp_user')
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 403

    @pytest.mark.parametrize('url', [
        '/admin/dashboard',
        '/admin/usuarios',
        '/admin/auditoria',
    ])
    def test_coordenador_bloqueado(self, client, coordinator, url):
        login(client, 'coord_user')
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 403

    @pytest.mark.parametrize('url', [
        '/admin/dashboard',
        '/admin/usuarios',
    ])
    def test_portaria_bloqueada(self, client, security_user, url):
        login(client, 'security_user')
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 403


class TestAcessoNegadoCoordinator:
    """Funcionário e portaria não acessam área de coordenador."""

    @pytest.mark.parametrize('url', [
        '/coordenador/dashboard',
        '/coordenador/funcionarios',
        '/coordenador/motoristas',
        '/coordenador/motoristas/novo',
        '/coordenador/reservas-motorista',
    ])
    def test_funcionario_bloqueado(self, client, employee, url):
        login(client, 'emp_user')
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 403

    @pytest.mark.parametrize('url', [
        '/coordenador/dashboard',
        '/coordenador/funcionarios',
    ])
    def test_portaria_bloqueada(self, client, security_user, url):
        login(client, 'security_user')
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 403


class TestAcessoNegadoEmployee:
    """Portaria não cria solicitações."""

    def test_portaria_nao_acessa_solicitar(self, client, security_user, vehicle):
        login(client, 'security_user')
        r = client.get('/funcionario/solicitar', follow_redirects=False)
        assert r.status_code == 403

    def test_portaria_nao_acessa_dashboard_employee(self, client, security_user):
        login(client, 'security_user')
        r = client.get('/funcionario/dashboard', follow_redirects=False)
        assert r.status_code == 403


class TestAcessoNegadoPortaria:
    """Somente portaria acessa /portaria/*."""

    def test_funcionario_bloqueado(self, client, employee):
        login(client, 'emp_user')
        r = client.get('/portaria/dashboard', follow_redirects=False)
        assert r.status_code == 403

    def test_coordenador_bloqueado(self, client, coordinator):
        login(client, 'coord_user')
        r = client.get('/portaria/dashboard', follow_redirects=False)
        assert r.status_code == 403

    def test_admin_bloqueado(self, client, admin):
        login(client, 'admin_user')
        r = client.get('/portaria/dashboard', follow_redirects=False)
        assert r.status_code == 403


# ── IDs inexistentes ──────────────────────────────────────────────────────────

class TestIdInexistente:
    @pytest.mark.parametrize('url', [
        '/admin/usuarios/99999/editar',
        '/admin/veiculos/99999/editar',
    ])
    def test_admin_id_inexistente(self, client, admin, url):
        login(client, 'admin_user')
        assert client.get(url).status_code == 404

    @pytest.mark.parametrize('url', [
        '/coordenador/funcionarios/99999/editar',
        '/coordenador/motoristas/99999/editar',
    ])
    def test_coordenador_id_inexistente(self, client, coordinator, url):
        login(client, 'coord_user')
        r = client.get(url)
        assert r.status_code in (403, 404)

    def test_portaria_solicitacao_inexistente(self, client, security_user):
        login(client, 'security_user')
        r = client.post('/portaria/solicitacao/99999/saiu', data={})
        assert r.status_code == 404

    def test_portaria_reserva_inexistente(self, client, security_user):
        login(client, 'security_user')
        r = client.post('/portaria/reserva/99999/saiu', data={})
        assert r.status_code == 404

    def test_coordenador_aprovar_inexistente(self, client, coordinator):
        login(client, 'coord_user')
        r = client.post('/coordenador/solicitacao/99999/aprovar', data={'vehicle_id': '1'})
        assert r.status_code == 404

    def test_coordenador_recusar_inexistente(self, client, coordinator):
        login(client, 'coord_user')
        r = client.post('/coordenador/solicitacao/99999/recusar', data={'notes': 'x'})
        assert r.status_code == 404


# ── IDs com valor zero ou negativo ────────────────────────────────────────────

class TestIdZeroNegativo:
    @pytest.mark.parametrize('user_id', [0, -1, -999])
    def test_admin_usuario_id_invalido(self, client, admin, user_id):
        login(client, 'admin_user')
        r = client.get(f'/admin/usuarios/{user_id}/editar')
        assert r.status_code == 404

    @pytest.mark.parametrize('vehicle_id', [0, -1])
    def test_admin_veiculo_id_invalido(self, client, admin, vehicle_id):
        login(client, 'admin_user')
        r = client.get(f'/admin/veiculos/{vehicle_id}/editar')
        assert r.status_code == 404


# ── Métodos HTTP incorretos ───────────────────────────────────────────────────

class TestMetodoErrado:
    """GET em rotas só-POST deve retornar 405, não 500."""

    @pytest.mark.parametrize('url', [
        '/coordenador/solicitacao/1/aprovar',
        '/coordenador/solicitacao/1/recusar',
        '/portaria/solicitacao/1/saiu',
        '/portaria/solicitacao/1/voltou',
        '/portaria/reserva/1/saiu',
        '/portaria/reserva/1/voltou',
        '/conta/solicitar-exclusao',
    ])
    def test_get_em_rota_post(self, client, admin, url):
        login(client, 'admin_user')
        r = client.get(url)
        assert r.status_code in (403, 404, 405), \
            f"Esperava 403/404/405 em GET {url}, recebeu {r.status_code}"


# ── Acesso cruzado entre usuários ─────────────────────────────────────────────

class TestAcessoCruzado:
    """Coordenador não edita funcionários de outro coordenador."""

    def _create_emp_of_coord2(self, app, coordinator2):
        """Cria um funcionário que pertence APENAS ao coordinator2."""
        from app.models import User, Role
        from app.extensions import db
        from datetime import datetime, timezone
        with app.app_context():
            emp = User(username='emp_alheio', email='emp_alheio@test.com',
                       full_name='Emp Alheio', role=Role.EMPLOYEE, is_active=True,
                       consent_accepted_at=datetime.now(timezone.utc))
            emp.set_password('Senha123')
            coord2 = db.session.get(User, coordinator2)
            emp.coordinators.append(coord2)
            db.session.add(emp)
            db.session.commit()
            return emp.id

    def test_coordenador_nao_edita_funcionario_alheio(
            self, client, app, coordinator, coordinator2):
        emp_alheio_id = self._create_emp_of_coord2(app, coordinator2)
        login(client, 'coord_user')
        r = client.get(f'/coordenador/funcionarios/{emp_alheio_id}/editar')
        assert r.status_code in (403, 404)

    def test_coordenador_nao_aprova_solicitacao_alheia(
            self, client, app, coordinator, coordinator2, vehicle):
        emp_alheio_id = self._create_emp_of_coord2(app, coordinator2)
        from app.models import VehicleRequest, RequestStatus
        from app.extensions import db
        from datetime import datetime, timedelta
        with app.app_context():
            vr = VehicleRequest(
                employee_id=emp_alheio_id,
                vehicle_id=vehicle,
                departure_datetime=datetime.now() + timedelta(hours=1),
                expected_return_datetime=datetime.now() + timedelta(hours=5),
                reason='Teste alheio', returns_to_company=True,
                status=RequestStatus.PENDING,
            )
            db.session.add(vr)
            db.session.commit()
            vr_id = vr.id

        login(client, 'coord_user')
        r = client.post(f'/coordenador/solicitacao/{vr_id}/aprovar',
                        data={'vehicle_id': str(vehicle)})
        assert r.status_code == 403


# ── Sem autenticação ──────────────────────────────────────────────────────────

class TestSemAutenticacao:
    @pytest.mark.parametrize('url', [
        '/funcionario/dashboard',
        '/funcionario/solicitar',
        '/coordenador/dashboard',
        '/portaria/dashboard',
        '/admin/dashboard',
        '/conta/trocar-senha',
        '/conta/meus-dados',
        '/conta/exportar-dados',
        '/relatorios/',
    ])
    def test_rota_protegida_redireciona_login(self, client, url):
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 302
        assert '/login' in r.headers['Location']

    def test_post_sem_autenticacao(self, client):
        r = client.post('/conta/solicitar-exclusao', data={}, follow_redirects=False)
        assert r.status_code == 302
        assert '/login' in r.headers['Location']
