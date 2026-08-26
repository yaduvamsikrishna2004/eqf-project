from fastapi import APIRouter, Depends, Query

from api.dependencies import get_analytics_service, require_roles
from services.analytics_service import AnalyticsService


router = APIRouter(prefix='/api/management', tags=['management'])


def _collect_filters(search: str | None, date_from: str | None, date_to: str | None, oem: str | None, severity: str | None, status: str | None, issue_type: str | None, custodian: str | None, vehicle_variant: str | None) -> dict:
    return {
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'oem': oem,
        'severity': severity,
        'status': status,
        'issue_type': issue_type,
        'custodian': custodian,
        'vehicle_variant': vehicle_variant,
    }


@router.get('/summary')
def get_summary(
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    oem: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    issue_type: str | None = Query(default=None, alias='issueType'),
    custodian: str | None = None,
    vehicle_variant: str | None = Query(default=None, alias='vehicleVariant'),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user=Depends(require_roles('Admin', 'Manager')),
):
    return analytics_service.get_summary(_collect_filters(search, date_from, date_to, oem, severity, status, issue_type, custodian, vehicle_variant))


@router.get('/analytics')
def get_analytics(
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    oem: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    issue_type: str | None = Query(default=None, alias='issueType'),
    custodian: str | None = None,
    vehicle_variant: str | None = Query(default=None, alias='vehicleVariant'),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user=Depends(require_roles('Admin', 'Manager')),
):
    return analytics_service.get_analytics(_collect_filters(search, date_from, date_to, oem, severity, status, issue_type, custodian, vehicle_variant))


@router.get('/incidents')
def list_management_incidents(
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    oem: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    issue_type: str | None = Query(default=None, alias='issueType'),
    custodian: str | None = None,
    vehicle_variant: str | None = Query(default=None, alias='vehicleVariant'),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user=Depends(require_roles('Admin', 'Manager')),
):
    return analytics_service.list_incidents(_collect_filters(search, date_from, date_to, oem, severity, status, issue_type, custodian, vehicle_variant))
