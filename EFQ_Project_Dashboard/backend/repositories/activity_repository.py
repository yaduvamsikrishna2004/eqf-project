from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ActivityRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def add(self, activity_row: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def list_by_incident_id(self, incident_id: str) -> list[dict[str, Any]]: ...


class ExcelActivityRepository(ActivityRepository):
    def __init__(self, manager) -> None:
        self.manager = manager

    def list_all(self) -> list[dict[str, Any]]:
        return self.manager.read_rows('Activities')

    def add(self, activity_row: dict[str, Any]) -> dict[str, Any]:
        rows = self.list_all()
        rows.append(activity_row)
        self.manager.replace_rows('Activities', rows)
        return activity_row

    def list_by_incident_id(self, incident_id: str) -> list[dict[str, Any]]:
        return [row for row in self.list_all() if row['IncidentID'] == incident_id]
