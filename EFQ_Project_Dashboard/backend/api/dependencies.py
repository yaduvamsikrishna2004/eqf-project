from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from config import get_settings
from services.auth_service import AuthService
from services.analytics_service import AnalyticsService
from services.incident_service import IncidentService
from services.resolution_service import ResolutionService


def get_repositories(request: Request):
    return request.app.state.repositories


def get_auth_service(request: Request, repositories=Depends(get_repositories)) -> AuthService:
    return AuthService(repositories, request.app.state.settings)


def get_incident_service(repositories=Depends(get_repositories)) -> IncidentService:
    return IncidentService(repositories)


def get_resolution_service(repositories=Depends(get_repositories)) -> ResolutionService:
    return ResolutionService(repositories)


def get_analytics_service(repositories=Depends(get_repositories)) -> AnalyticsService:
    return AnalyticsService(repositories)


def get_current_user(request: Request, auth_service: AuthService = Depends(get_auth_service)):
    token = request.cookies.get(request.app.state.settings.cookie_name)
    return auth_service.get_user_from_token(token)


def require_roles(*roles: str):
    def dependency(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You do not have access to this module.')
        return current_user

    return dependency
