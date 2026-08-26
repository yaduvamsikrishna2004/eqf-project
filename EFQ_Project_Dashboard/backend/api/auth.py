from fastapi import APIRouter, Depends, Response, status

from api.dependencies import get_auth_service, get_current_user
from models.user import AuthResponse, UserSigninRequest, UserSignupRequest
from services.auth_service import AuthService


router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/signup', response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserSignupRequest, auth_service: AuthService = Depends(get_auth_service)):
    user = auth_service.signup(payload)
    return {'user': user}


@router.post('/signin', response_model=AuthResponse)
def signin(payload: UserSigninRequest, response: Response, auth_service: AuthService = Depends(get_auth_service)):
    user, session_token = auth_service.signin(payload)
    response.set_cookie(
        key=auth_service.settings.cookie_name,
        value=session_token,
        httponly=True,
        secure=auth_service.settings.allow_cookie_secure,
        samesite='lax',
        max_age=auth_service.settings.session_max_age_seconds,
    )
    return {'user': user}


@router.post('/signout', status_code=status.HTTP_204_NO_CONTENT)
def signout(response: Response, auth_service: AuthService = Depends(get_auth_service)):
    response.delete_cookie(auth_service.settings.cookie_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/me', response_model=AuthResponse)
def me(current_user=Depends(get_current_user)):
    return {'user': current_user}
