from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import bcrypt
from itsdangerous import BadSignature, BadTimeSignature, URLSafeTimedSerializer


SESSION_SALT = 'efq-session'


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_ntid(value: str) -> str:
    return value.strip().upper()


def normalize_phone(value: str) -> str:
    return ''.join(char for char in value.strip() if char.isdigit() or char == '+')


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


class SessionSigner:
    def __init__(self, secret_key: str) -> None:
        self._serializer = URLSafeTimedSerializer(secret_key=secret_key, salt=SESSION_SALT)

    def dumps(self, payload: dict[str, Any]) -> str:
        return self._serializer.dumps(payload)

    def loads(self, token: str, max_age: int) -> dict[str, Any] | None:
        try:
            return self._serializer.loads(token, max_age=max_age)
        except (BadSignature, BadTimeSignature):
            return None
