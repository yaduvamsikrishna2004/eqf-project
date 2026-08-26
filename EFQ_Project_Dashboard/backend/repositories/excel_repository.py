from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repositories.activity_repository import ExcelActivityRepository
from repositories.incident_repository import ExcelIncidentRepository
from repositories.resolution_repository import ExcelResolutionRepository
from repositories.user_repository import ExcelUserRepository
from utils.excel_utils import WorkbookManager


class ExcelLookupRepository:
    def __init__(self, manager: WorkbookManager) -> None:
        self.manager = manager

    def list_oems(self) -> list[dict[str, Any]]:
        return [row for row in self.manager.read_rows('OEMRegions') if row['IsActive'] in (True, 'True', 'true', 1, '1')]

    def list_regions(self) -> list[dict[str, Any]]:
        return self.list_oems()

    def list_complaints(self) -> list[dict[str, Any]]:
        return [row for row in self.manager.read_rows('ComplaintSuggestions') if row['IsActive'] in (True, 'True', 'true', 1, '1')]

    def list_ecus(self) -> list[dict[str, Any]]:
        return [row for row in self.manager.read_rows('ECUs') if row['IsActive'] in (True, 'True', 'true', 1, '1')]

    def list_detection_phases(self) -> list[dict[str, Any]]:
        return [row for row in self.manager.read_rows('DetectionPhases') if row['IsActive'] in (True, 'True', 'true', 1, '1')]


@dataclass
class RepositoryContainer:
    manager: WorkbookManager
    users: ExcelUserRepository
    incidents: ExcelIncidentRepository
    resolutions: ExcelResolutionRepository
    activities: ExcelActivityRepository
    lookups: ExcelLookupRepository

    @classmethod
    def build(cls, file_path: Path) -> 'RepositoryContainer':
        manager = WorkbookManager(file_path)
        manager.ensure_workbook()
        return cls(
            manager=manager,
            users=ExcelUserRepository(manager),
            incidents=ExcelIncidentRepository(manager),
            resolutions=ExcelResolutionRepository(manager),
            activities=ExcelActivityRepository(manager),
            lookups=ExcelLookupRepository(manager),
        )
