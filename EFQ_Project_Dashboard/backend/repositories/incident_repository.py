from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IncidentRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_by_id(self, incident_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def create(self, incident_row: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def update(self, incident_id: str, updates: dict[str, Any]) -> dict[str, Any]: ...


class ExcelIncidentRepository(IncidentRepository):
    def __init__(self, manager) -> None:
        self.manager = manager

    def list_all(self) -> list[dict[str, Any]]:
        return self.manager.read_rows('Incidents')

    def get_by_id(self, incident_id: str) -> dict[str, Any] | None:
        for row in self.list_all():
            if row['IncidentID'] == incident_id:
                return row
        return None

    def create(self, incident_row: dict[str, Any]) -> dict[str, Any]:
        rows = self.list_all()
        rows.append(incident_row)
        self.manager.replace_rows('Incidents', rows)
        return incident_row

    def update(self, incident_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        rows = self.list_all()
        for row in rows:
            if row['IncidentID'] == incident_id:
                row.update(updates)
                self.manager.replace_rows('Incidents', rows)
                return row
        raise KeyError(f'Incident not found: {incident_id}')
