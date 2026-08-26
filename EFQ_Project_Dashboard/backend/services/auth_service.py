from __future__ import annotations

from fastapi import HTTPException, status

from models.user import UserResponse, UserSigninRequest, UserSignupRequest
from utils.security import SessionSigner, hash_password, normalize_ntid, normalize_phone, now_iso, verify_password


class AuthService:
    def __init__(self, repositories, settings) -> None:
        self.repositories = repositories
        self.settings = settings
        self.signer = SessionSigner(settings.secret_key)

    def signup(self, payload: UserSignupRequest) -> UserResponse:
        existing_user = self.repositories.users.get_by_ntid(payload.ntid)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='NT ID already exists.')

        timestamp = now_iso()
        user_id = f"USR-{len(self.repositories.users.list_all()) + 1:06d}"
        user_row = {
            'UserID': user_id,
            'FullName': payload.full_name.strip(),
            'NTID': normalize_ntid(payload.ntid),
            'Phone': normalize_phone(payload.phone),
            'Email': payload.email.lower(),
            'Role': payload.role,
            'PasswordHash': hash_password(payload.password),
            'AccountStatus': 'Active',
            'CreatedAt': timestamp,
            'UpdatedAt': timestamp,
            'LastLoginAt': '',
        }
        created_user = self.repositories.users.create(user_row)
        return self._serialize_user(created_user)

    def signin(self, payload: UserSigninRequest) -> tuple[UserResponse, str]:
        user_row = self.repositories.users.get_by_ntid(payload.ntid)
        if not user_row or not verify_password(payload.password, user_row['PasswordHash']):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid NT ID or password.')
        if user_row['AccountStatus'] != 'Active':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Account is not active.')

        login_time = now_iso()
        updated_user = self.repositories.users.update(user_row['NTID'], {'LastLoginAt': login_time, 'UpdatedAt': login_time})
        session_token = self.signer.dumps({'ntid': updated_user['NTID']})
        return self._serialize_user(updated_user), session_token

    def get_user_from_token(self, token: str | None):
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required.')
        payload = self.signer.loads(token, max_age=self.settings.session_max_age_seconds)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Session expired. Please sign in again.')
        user_row = self.repositories.users.get_by_ntid(payload['ntid'])
        if not user_row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User session is invalid.')
        return self._serialize_user(user_row)

    @staticmethod
    def _serialize_user(row: dict) -> UserResponse:
        return UserResponse(
            user_id=row['UserID'],
            full_name=row['FullName'],
            ntid=row['NTID'],
            phone=row['Phone'],
            email=row['Email'],
            role=row['Role'],
            account_status=row['AccountStatus'],
            created_at=row['CreatedAt'],
            updated_at=row['UpdatedAt'],
            last_login_at=row.get('LastLoginAt') or None,
        )
