from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


UserRole = Literal['Admin', 'Manager', 'Custodian', 'Other']


class UserSignupRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    ntid: str = Field(min_length=1, max_length=40)
    phone: str = Field(min_length=7, max_length=30)
    email: EmailStr
    role: UserRole
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator('full_name', 'ntid', 'phone')
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator('ntid')
    @classmethod
    def normalize_ntid(cls, value: str) -> str:
        return value.upper()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value: str) -> str:
        cleaned = ''.join(char for char in value if char.isdigit() or char == '+')
        if not re.fullmatch(r'\+?[0-9]{7,15}', cleaned):
            raise ValueError('Enter a valid phone number.')
        return cleaned

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not re.search(r'[A-Z]', value):
            raise ValueError('Password must include an uppercase letter.')
        if not re.search(r'[a-z]', value):
            raise ValueError('Password must include a lowercase letter.')
        if not re.search(r'[0-9]', value):
            raise ValueError('Password must include a number.')
        return value

    @model_validator(mode='after')
    def passwords_match(self) -> 'UserSignupRequest':
        if self.password != self.confirm_password:
            raise ValueError('Confirm password must match password.')
        return self


class UserSigninRequest(BaseModel):
    ntid: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=1, max_length=128)

    @field_validator('ntid')
    @classmethod
    def normalize_ntid(cls, value: str) -> str:
        return value.strip().upper()


class UserResponse(BaseModel):
    user_id: str
    full_name: str
    ntid: str
    phone: str
    email: EmailStr
    role: UserRole
    account_status: str
    created_at: str
    updated_at: str
    last_login_at: str | None = None


class AuthResponse(BaseModel):
    user: UserResponse


class CustodianOption(BaseModel):
    ntid: str
    full_name: str
