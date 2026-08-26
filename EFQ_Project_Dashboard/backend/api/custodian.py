from fastapi import APIRouter, Depends

from api.dependencies import get_resolution_service, require_roles
from models.resolution import ResolutionUpdateRequest
from services.resolution_service import ResolutionService


router = APIRouter(prefix='/api/custodian', tags=['custodian'])


@router.get('/incidents')
def list_custodian_incidents(
    resolution_service: ResolutionService = Depends(get_resolution_service),
    current_user=Depends(require_roles('Admin', 'Custodian')),
):
    return resolution_service.list_incidents_for_custodian(current_user)


@router.get('/incidents/{incident_id}')
def get_custodian_incident(
    incident_id: str,
    resolution_service: ResolutionService = Depends(get_resolution_service),
    current_user=Depends(require_roles('Admin', 'Custodian')),
):
    return resolution_service.get_incident_detail(incident_id, current_user)


@router.put('/incidents/{incident_id}/resolution')
def update_resolution(
    incident_id: str,
    payload: ResolutionUpdateRequest,
    resolution_service: ResolutionService = Depends(get_resolution_service),
    current_user=Depends(require_roles('Admin', 'Custodian')),
):
    return resolution_service.update_resolution(incident_id, payload, current_user)


@router.get('/incidents/{incident_id}/activities')
def list_activities(
    incident_id: str,
    resolution_service: ResolutionService = Depends(get_resolution_service),
    current_user=Depends(require_roles('Admin', 'Custodian')),
):
    return resolution_service.list_activities(incident_id, current_user)
