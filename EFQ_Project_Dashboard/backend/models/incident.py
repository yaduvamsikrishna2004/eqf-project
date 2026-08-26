from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


Severity = Literal['Low', 'Medium', 'High', 'Critical']
IssueType = Literal['0 KM', 'Field Issue']
IncidentStatus = Literal['Draft', 'New', 'Investigation Started', 'Root Cause Identified', 'Action In Progress', 'Validation', 'Closed']


class IncidentCreateRequest(BaseModel):
    incident_title: str | None = Field(default=None, max_length=150)
    date: date
    oem: str = Field(min_length=1, max_length=120)
    customer_complaint: str = Field(min_length=1, max_length=1000)
    dealer_name: str = Field(min_length=1, max_length=120)
    dealer_location: str = Field(min_length=1, max_length=120)
    dealer_contact: str = Field(min_length=1, max_length=40)
    vehicle_model: str = Field(min_length=1, max_length=120)
    vehicle_variant: str = Field(min_length=1, max_length=120)
    vehicle_application: str = Field(min_length=1, max_length=120)
    vin: str = Field(min_length=5, max_length=30)
    kilometer_reading: int = Field(ge=0)
    ecu_part_number: str = Field(min_length=1, max_length=120)
    ecu_name: str = Field(min_length=1, max_length=120)
    severity: Severity
    issue_type: IssueType
    custodian_ntid: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=1, max_length=4000)
    draft: bool = False

    @field_validator('oem', 'customer_complaint', 'dealer_name', 'dealer_location', 'dealer_contact', 'vehicle_model', 'vehicle_variant', 'vehicle_application', 'ecu_part_number', 'ecu_name', 'description', 'custodian_ntid')
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator('custodian_ntid')
    @classmethod
    def normalize_ntid(cls, value: str) -> str:
        return value.upper()

    @field_validator('vin')
    @classmethod
    def uppercase_vin(cls, value: str) -> str:
        return value.strip().upper()


class IncidentUpdateRequest(BaseModel):
    date: date | None = None
    oem: str | None = None
    customer_complaint: str | None = None
    dealer_name: str | None = None
    dealer_location: str | None = None
    dealer_contact: str | None = None
    vehicle_model: str | None = None
    vehicle_variant: str | None = None
    vehicle_application: str | None = None
    vin: str | None = None
    kilometer_reading: int | None = Field(default=None, ge=0)
    ecu_part_number: str | None = None
    ecu_name: str | None = None
    severity: Severity | None = None
    issue_type: IssueType | None = None
    custodian_ntid: str | None = None
    description: str | None = None

    @field_validator('custodian_ntid')
    @classmethod
    def normalize_ntid(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value

    @field_validator('vin')
    @classmethod
    def uppercase_vin(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value


class IncidentResponse(BaseModel):
    incident_id: str
    incident_title: str
    date: str
    oem: str
    customer_complaint: str
    dealer_name: str
    dealer_location: str
    dealer_contact: str
    vehicle_model: str
    vehicle_variant: str
    vehicle_application: str
    vin: str
    kilometer_reading: int
    ecu_part_number: str
    ecu_name: str
    severity: Severity
    issue_type: IssueType
    custodian_ntid: str
    custodian_name: str
    description: str
    status: str
    created_by: str
    created_at: str
    updated_by: str
    updated_at: str
