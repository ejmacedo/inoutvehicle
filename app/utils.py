from app.extensions import db
from app.models import VehicleRequest, DriverReservation, RequestStatus


def get_unavailable_vehicle_ids():
    """
    Retorna o conjunto de IDs de veículos que estão atualmente
    indisponíveis (aprovados e ainda não retornados).
    Um veículo só fica disponível novamente quando a portaria
    registrar o retorno real (actual_return_datetime).
    """
    vr_ids = {r.vehicle_id for r in VehicleRequest.query.filter(
        VehicleRequest.status == RequestStatus.APPROVED,
        VehicleRequest.actual_return_datetime.is_(None),
    ).all()}

    dr_ids = {r.vehicle_id for r in DriverReservation.query.filter(
        DriverReservation.actual_return_datetime.is_(None),
    ).all()}

    return vr_ids | dr_ids
