from fastapi import APIRouter, Depends

from api.dependencies import get_repositories, require_roles


router = APIRouter(prefix='/api/lookups', tags=['lookups'])


@router.get('/oems')
def get_oems(repositories=Depends(get_repositories), current_user=Depends(require_roles('Admin', 'Manager', 'Custodian', 'Other'))):
    return repositories.lookups.list_oems()


@router.get('/regions')
def get_regions(repositories=Depends(get_repositories), current_user=Depends(require_roles('Admin', 'Manager', 'Custodian', 'Other'))):
    return repositories.lookups.list_regions()


@router.get('/complaints')
def get_complaints(repositories=Depends(get_repositories), current_user=Depends(require_roles('Admin', 'Manager', 'Custodian', 'Other'))):
    return repositories.lookups.list_complaints()


@router.get('/ecus')
def get_ecus(repositories=Depends(get_repositories), current_user=Depends(require_roles('Admin', 'Manager', 'Custodian', 'Other'))):
    return repositories.lookups.list_ecus()


@router.get('/detection-phases')
def get_detection_phases(repositories=Depends(get_repositories), current_user=Depends(require_roles('Admin', 'Manager', 'Custodian', 'Other'))):
    return repositories.lookups.list_detection_phases()
