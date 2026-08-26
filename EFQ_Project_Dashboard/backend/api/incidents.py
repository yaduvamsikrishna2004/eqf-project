from fastapi import APIRouter, Depends

from api.dependencies import get_incident_service, require_roles
from models.incident import IncidentCreateRequest, IncidentUpdateRequest
from services.incident_service import IncidentService


router = APIRouter(tags=['incidents'])


@router.get('/api/users/custodians')
def list_custodians(
    incident_service: IncidentService = Depends(get_incident_service),
    current_user=Depends(require_roles('Admin', 'Manager', 'Custodian', 'Other')),
):
    return incident_service.list_custodians()


@router.post('/api/incidents')
def create_incident(
    payload: IncidentCreateRequest,
    incident_service: IncidentService = Depends(get_incident_service),
    current_user=Depends(require_roles('Admin', 'Manager', 'Custodian', 'Other')),
):
    return incident_service.create_incident(payload, current_user)


@router.get('/api/incidents/{incident_id}')
def get_incident(
    incident_id: str,
    incident_service: IncidentService = Depends(get_incident_service),
    current_user=Depends(require_roles('Admin', 'Manager', 'Custodian', 'Other')),
):
    return incident_service.get_incident(incident_id)


@router.put('/api/incidents/{incident_id}')
def update_incident(
    incident_id: str,
    payload: IncidentUpdateRequest,
    incident_service: IncidentService = Depends(get_incident_service),
    current_user=Depends(require_roles('Admin', 'Manager', 'Custodian', 'Other')),
):
    return incident_service.update_incident(incident_id, payload, current_user)


@router.post('/api/incidents/{incident_id}/submit')
def submit_incident(
    incident_id: str,
    incident_service: IncidentService = Depends(get_incident_service),
    current_user=Depends(require_roles('Admin', 'Manager', 'Custodian', 'Other')),
):
    return incident_service.submit_incident(incident_id, current_user)
