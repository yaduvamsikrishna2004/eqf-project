from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


ValidationResult = Literal['Not Tested', 'Pass', 'Fail', 'Conditional Pass']
ResolutionStatus = Literal['Not Started', 'Investigation', 'Root Cause Identified', 'Action In Progress', 'Validation', 'Closed']


class ResolutionUpdateRequest(BaseModel):
    investigation_details: str = Field(default='', max_length=4000)
    root_cause: str = Field(default='', max_length=4000)
    recommendation: str = Field(default='', max_length=4000)
    proposed_solution: str = Field(default='', max_length=4000)
    corrective_action: str = Field(default='', max_length=4000)
    preventive_action: str = Field(default='', max_length=4000)
    validation_method: str = Field(default='', max_length=1000)
    validation_result: ValidationResult = 'Not Tested'
    validation_date: date | None = None
    target_date: date | None = None
    resolution_status: ResolutionStatus = 'Not Started'
    remarks: str = Field(default='', max_length=2000)


class ResolutionResponse(BaseModel):
    resolution_id: str
    incident_id: str
    investigation_details: str
    root_cause: str
    recommendation: str
    proposed_solution: str
    corrective_action: str
    preventive_action: str
    validation_method: str
    validation_result: ValidationResult
    validation_date: str | None = None
    resolution_owner: str
    target_date: str | None = None
    resolution_date: str | None = None
    resolution_status: str
    remarks: str
    created_at: str
    updated_at: str


class ActivityResponse(BaseModel):
    activity_id: str
    incident_id: str
    action: str
    user_ntid: str
    user_name: str
    timestamp: str
