"""Testes de relatórios: visualização, exportação Excel e PDF."""
from tests.conftest import login
from app.models import VehicleRequest, RequestStatus
from app.extensions import db
from datetime import datetime, timedelta


def _make_request(app, employee_id, vehicle_id, status=RequestStatus.APPROVED):
    with app.app_context():
        vr = VehicleRequest(
            employee_id=employee_id,
            vehicle_id=vehicle_id,
            departure_datetime=datetime.now() - timedelta(hours=3),
            expected_return_datetime=datetime.now() + timedelta(hours=2),
            reason='Visita técnica ao cliente para revisão de contrato.',
            returns_to_company=True,
            status=status,
        )
        db.session.add(vr)
        db.session.commit()
        return vr.id


class TestRelatoriosAcesso:
    def test_admin_acessa_relatorios(self, client, admin):
        login(client, 'admin_user')
        r = client.get('/relatorios/')
        assert r.status_code == 200
        assert b'Relat' in r.data

    def test_coordenador_acessa_relatorios(self, client, coordinator):
        login(client, 'coord_user')
        r = client.get('/relatorios/')
        assert r.status_code == 200

    def test_funcionario_nao_acessa_relatorios(self, client, employee):
        login(client, 'emp_user')
        r = client.get('/relatorios/', follow_redirects=True)
        assert r.status_code == 403

    def test_portaria_nao_acessa_relatorios(self, client, security_user):
        login(client, 'security_user')
        r = client.get('/relatorios/', follow_redirects=True)
        assert r.status_code == 403


class TestRelatoriosFiltros:
    def test_filtro_por_status_aprovado(self, client, app, admin, employee, vehicle):
        _make_request(app, employee, vehicle, status=RequestStatus.APPROVED)
        _make_request(app, employee, vehicle, status=RequestStatus.REJECTED)
        login(client, 'admin_user')
        r = client.get('/relatorios/?status=approved')
        assert r.status_code == 200
        # Badge de resultado aprovado presente; badge de recusado ausente nos resultados
        assert b'badge bg-success">Aprovado' in r.data
        assert b'badge bg-danger">Recusado' not in r.data

    def test_filtro_por_status_recusado(self, client, app, admin, employee, vehicle):
        _make_request(app, employee, vehicle, status=RequestStatus.APPROVED)
        _make_request(app, employee, vehicle, status=RequestStatus.REJECTED)
        login(client, 'admin_user')
        r = client.get('/relatorios/?status=rejected')
        assert r.status_code == 200
        assert b'badge bg-danger">Recusado' in r.data
        assert b'badge bg-success">Aprovado' not in r.data

    def test_filtro_por_employee(self, client, app, admin, employee, vehicle):
        _make_request(app, employee, vehicle)
        login(client, 'admin_user')
        r = client.get(f'/relatorios/?employee_id={employee}')
        assert r.status_code == 200

    def test_filtro_por_veiculo(self, client, app, admin, employee, vehicle):
        _make_request(app, employee, vehicle)
        login(client, 'admin_user')
        r = client.get(f'/relatorios/?vehicle_id={vehicle}')
        assert r.status_code == 200

    def test_sem_filtros_nao_exibe_resultados(self, client, app, admin, employee, vehicle):
        _make_request(app, employee, vehicle)
        login(client, 'admin_user')
        r = client.get('/relatorios/')
        # Sem nenhum filtro ativo, não exibe badges de resultado
        assert b'badge bg-success">Aprovado' not in r.data

    def test_coordenador_so_ve_seus_funcionarios(self, client, app, coordinator,
                                                   coordinator2, employee, vehicle):
        """Coordenador não vê solicitações de funcionários de outro coordenador."""
        with app.app_context():
            from app.models import User, Role
            emp_other = User(username='emp_other', email='emp_other@test.com',
                             full_name='Emp Other', role=Role.EMPLOYEE, is_active=True)
            emp_other.set_password('senha123')
            coord2 = db.session.get(User, coordinator2)
            emp_other.coordinators.append(coord2)
            db.session.add(emp_other)
            db.session.commit()
            _make_request(app, emp_other.id, vehicle)

        login(client, 'coord_user')
        r = client.get('/relatorios/?status=approved')
        assert b'Emp Other' not in r.data


class TestExportacoes:
    def test_exportar_excel(self, client, app, admin, employee, vehicle):
        _make_request(app, employee, vehicle)
        login(client, 'admin_user')
        r = client.get('/relatorios/exportar/excel?status=approved')
        assert r.status_code == 200
        assert 'spreadsheetml' in r.content_type
        assert len(r.data) > 1000   # arquivo gerado tem conteúdo

    def test_exportar_pdf(self, client, app, admin, employee, vehicle):
        _make_request(app, employee, vehicle)
        login(client, 'admin_user')
        r = client.get('/relatorios/exportar/pdf?status=approved')
        assert r.status_code == 200
        assert r.content_type == 'application/pdf'
        assert r.data[:4] == b'%PDF'

    def test_exportar_excel_vazio(self, client, admin):
        login(client, 'admin_user')
        r = client.get('/relatorios/exportar/excel')
        assert r.status_code == 200
        assert 'spreadsheetml' in r.content_type

    def test_exportar_pdf_vazio(self, client, admin):
        login(client, 'admin_user')
        r = client.get('/relatorios/exportar/pdf')
        assert r.status_code == 200
        assert r.content_type == 'application/pdf'

    def test_funcionario_nao_exporta_excel(self, client, employee):
        login(client, 'emp_user')
        r = client.get('/relatorios/exportar/excel', follow_redirects=True)
        assert r.status_code == 403

    def test_coordenador_exporta_excel(self, client, app, coordinator, employee, vehicle):
        _make_request(app, employee, vehicle)
        login(client, 'coord_user')
        r = client.get('/relatorios/exportar/excel?status=approved')
        assert r.status_code == 200
        assert 'spreadsheetml' in r.content_type
