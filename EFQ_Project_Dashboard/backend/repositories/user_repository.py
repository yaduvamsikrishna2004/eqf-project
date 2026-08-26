from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from models.user import CustodianOption
from utils.security import normalize_ntid


class UserRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_by_ntid(self, ntid: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def create(self, user_row: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def update(self, ntid: str, updates: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def list_custodians(self) -> list[dict[str, Any]]: ...


class ExcelUserRepository(UserRepository):
    def __init__(self, manager) -> None:
        self.manager = manager

    def list_all(self) -> list[dict[str, Any]]:
        return self.manager.read_rows('Users')

    def get_by_ntid(self, ntid: str) -> dict[str, Any] | None:
        normalized = normalize_ntid(ntid)
        for row in self.list_all():
            if row['NTID'] == normalized:
                return row
        return None

    def create(self, user_row: dict[str, Any]) -> dict[str, Any]:
        rows = self.list_all()
        rows.append(user_row)
        self.manager.replace_rows('Users', rows)
        return user_row

    def update(self, ntid: str, updates: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_ntid(ntid)
        rows = self.list_all()
        for row in rows:
            if row['NTID'] == normalized:
                row.update(updates)
                self.manager.replace_rows('Users', rows)
                return row
        raise KeyError(f'User not found: {normalized}')

    def list_custodians(self) -> list[dict[str, Any]]:
        return [row for row in self.list_all() if row['Role'] == 'Custodian' and row['AccountStatus'] == 'Active']
