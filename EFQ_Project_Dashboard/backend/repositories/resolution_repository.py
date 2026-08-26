from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ResolutionRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_by_incident_id(self, incident_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def upsert(self, incident_id: str, resolution_row: dict[str, Any]) -> dict[str, Any]: ...


class ExcelResolutionRepository(ResolutionRepository):
    def __init__(self, manager) -> None:
        self.manager = manager

    def list_all(self) -> list[dict[str, Any]]:
        return self.manager.read_rows('Resolutions')

    def get_by_incident_id(self, incident_id: str) -> dict[str, Any] | None:
        for row in self.list_all():
            if row['IncidentID'] == incident_id:
                return row
        return None

    def upsert(self, incident_id: str, resolution_row: dict[str, Any]) -> dict[str, Any]:
        rows = self.list_all()
        updated = False
        for index, row in enumerate(rows):
            if row['IncidentID'] == incident_id:
                rows[index] = resolution_row
                updated = True
                break
        if not updated:
            rows.append(resolution_row)
        self.manager.replace_rows('Resolutions', rows)
        return resolution_row
