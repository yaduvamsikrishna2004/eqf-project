from __future__ import annotations
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config.config import (
    EXCEL_FILE,
    INCIDENTS_SHEET,
    RESOLUTIONS_SHEET,
    ACTIVITIES_SHEET,
    INCIDENT_ID_PREFIX,
    RESOLUTION_ID_PREFIX,
    ACTIVITY_ID_PREFIX,
)

# Column definitions
INCIDENT_COLUMNS = [
    "IncidentID",
    "Date",
    "OEM",
    "CustomerComplaint",
    "DealerInfo",
    "VehicleVariant",
    "VehicleApplication",
    "ECUPartNumber",
    "Severity",
    "IssueType",
    "Custodian",
    "Description",
    "Status",
    "CreatedAt",
    "UpdatedAt",
]

RESOLUTION_COLUMNS = [
    "ResolutionID",
    "IncidentID",
    "RootCause",
    "InvestigationDetails",
    "Recommendation",
    "ProposedSolution",
    "CorrectiveAction",
    "PreventiveAction",
    "ValidationMethod",
    "ValidationResult",
    "ResolutionOwner",
    "TargetDate",
    "ResolutionDate",
    "ResolutionStatus",
    "Remarks",
    "CreatedAt",
    "UpdatedAt",
]

ACTIVITY_COLUMNS = ["ActivityID", "IncidentID", "Action", "User", "Timestamp"]


def initialize_database() -> None:
    """Create Excel workbook with required sheets and headers if missing."""
    excel_path: Path = Path(EXCEL_FILE)
    # If file doesn't exist, create workbook with headers
    if not excel_path.exists():
        incidents_df = pd.DataFrame(columns=INCIDENT_COLUMNS)
        resolutions_df = pd.DataFrame(columns=RESOLUTION_COLUMNS)
        activities_df = pd.DataFrame(columns=ACTIVITY_COLUMNS)
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            incidents_df.to_excel(writer, sheet_name=INCIDENTS_SHEET, index=False)
            resolutions_df.to_excel(writer, sheet_name=RESOLUTIONS_SHEET, index=False)
            activities_df.to_excel(writer, sheet_name=ACTIVITIES_SHEET, index=False)
        return

    # If file exists, verify sheets and columns
    with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a") as writer:
        # read list of sheets
        try:
            existing = pd.ExcelFile(excel_path).sheet_names
        except Exception:
            # if file is corrupted, raise a user-friendly error
            raise
        if INCIDENTS_SHEET not in existing:
            pd.DataFrame(columns=INCIDENT_COLUMNS).to_excel(writer, sheet_name=INCIDENTS_SHEET, index=False)
        if RESOLUTIONS_SHEET not in existing:
            pd.DataFrame(columns=RESOLUTION_COLUMNS).to_excel(writer, sheet_name=RESOLUTIONS_SHEET, index=False)
        if ACTIVITIES_SHEET not in existing:
            pd.DataFrame(columns=ACTIVITY_COLUMNS).to_excel(writer, sheet_name=ACTIVITIES_SHEET, index=False)


def _read_sheet(sheet_name: str) -> pd.DataFrame:
    excel_path: Path = Path(EXCEL_FILE)
    try:
        if not excel_path.exists():
            initialize_database()
        df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")
    except ValueError:
        # sheet missing
        if sheet_name == INCIDENTS_SHEET:
            df = pd.DataFrame(columns=INCIDENT_COLUMNS)
        else:
            df = pd.DataFrame(columns=ACTIVITY_COLUMNS)
    return df


def get_incidents() -> pd.DataFrame:
    df = _read_sheet(INCIDENTS_SHEET)
    # ensure consistent columns
    for col in INCIDENT_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[INCIDENT_COLUMNS]


def get_activities() -> pd.DataFrame:
    df = _read_sheet(ACTIVITIES_SHEET)
    for col in ACTIVITY_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[ACTIVITY_COLUMNS]


def _next_id(existing_ids: pd.Series, prefix: str) -> str:
    """Compute next ID given existing ID series like EFQ-000001."""
    nums = []
    for val in existing_ids.dropna().astype(str):
        if val.startswith(prefix):
            try:
                nums.append(int(val.replace(prefix, "")))
            except ValueError:
                continue
    next_num = max(nums) + 1 if nums else 1
    return f"{prefix}{next_num:06d}"


def generate_incident_id() -> str:
    incidents = get_incidents()
    return _next_id(incidents.get("IncidentID", pd.Series(dtype=object)), INCIDENT_ID_PREFIX)


def generate_activity_id() -> str:
    acts = get_activities()
    return _next_id(acts.get("ActivityID", pd.Series(dtype=object)), ACTIVITY_ID_PREFIX)


def _save_sheet(df: pd.DataFrame, sheet_name: str) -> None:
    """Save only the given sheet; preserve other sheets."""
    excel_path: Path = Path(EXCEL_FILE)
    # pandas >=1.3 supports if_sheet_exists
    if excel_path.exists():
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def save_incidents(df: pd.DataFrame) -> None:
    df = df.copy()
    # ensure correct column order
    df = df.reindex(columns=INCIDENT_COLUMNS)
    _save_sheet(df, INCIDENTS_SHEET)


def save_activities(df: pd.DataFrame) -> None:
    df = df.copy()
    df = df.reindex(columns=ACTIVITY_COLUMNS)
    _save_sheet(df, ACTIVITIES_SHEET)


def log_activity(incident_id: str, action: str, user: str = "Admin") -> None:
    acts = get_activities()
    activity = {
        "ActivityID": generate_activity_id(),
        "IncidentID": incident_id,
        "Action": action,
        "User": user,
        "Timestamp": datetime.utcnow(),
    }
    acts = pd.concat([acts, pd.DataFrame([activity])], ignore_index=True)
    save_activities(acts)


def create_incident(incident_data: Dict[str, Any]) -> str:
    """Create a new incident and return its IncidentID."""
    incidents = get_incidents()
    # generate id and timestamps
    incident_id = generate_incident_id()
    now = datetime.utcnow()
    record = {col: None for col in INCIDENT_COLUMNS}
    record.update(incident_data)
    record["IncidentID"] = incident_id
    # Date may be a datetime.date or string; keep as-is
    record["CreatedAt"] = now
    record["UpdatedAt"] = now
    incidents = pd.concat([incidents, pd.DataFrame([record])], ignore_index=True)
    save_incidents(incidents)
    log_activity(incident_id, "Incident Created")
    return incident_id


def update_incident(incident_id: str, updates: Dict[str, Any]) -> bool:
    incidents = get_incidents()
    mask = incidents["IncidentID"] == incident_id
    if not mask.any():
        return False
    # Do not allow changing IncidentID or CreatedAt
    updates = {k: v for k, v in updates.items() if k not in ("IncidentID", "CreatedAt")}
    for k, v in updates.items():
        if k in incidents.columns:
            incidents.loc[mask, k] = v
    incidents.loc[mask, "UpdatedAt"] = datetime.utcnow()
    save_incidents(incidents)
    log_activity(incident_id, "Incident Updated")
    return True


def delete_incident(incident_id: str) -> bool:
    incidents = get_incidents()
    if incident_id not in incidents.get("IncidentID", []).astype(str).values:
        return False
    incidents = incidents[incidents["IncidentID"] != incident_id]
    save_incidents(incidents)
    log_activity(incident_id, "Incident Deleted")
    return True


def get_resolutions() -> pd.DataFrame:
    df = _read_sheet(RESOLUTIONS_SHEET)
    for col in RESOLUTION_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[RESOLUTION_COLUMNS]


def get_resolution_by_incident(incident_id: str) -> Optional[Dict[str, Any]]:
    """Get resolution record for a specific incident."""
    resolutions = get_resolutions()
    matching = resolutions[resolutions["IncidentID"] == incident_id]
    if matching.empty:
        return None
    return matching.iloc[0].to_dict()


def generate_resolution_id() -> str:
    resolutions = get_resolutions()
    return _next_id(resolutions.get("ResolutionID", pd.Series(dtype=object)), RESOLUTION_ID_PREFIX)


def save_resolutions(df: pd.DataFrame) -> None:
    df = df.copy()
    df = df.reindex(columns=RESOLUTION_COLUMNS)
    _save_sheet(df, RESOLUTIONS_SHEET)


def create_resolution(incident_id: str, resolution_data: Dict[str, Any]) -> str:
    """Create or get a resolution record for an incident."""
    resolutions = get_resolutions()
    # Check if resolution already exists
    existing = resolutions[resolutions["IncidentID"] == incident_id]
    if not existing.empty:
        return existing.iloc[0]["ResolutionID"]
    
    now = datetime.utcnow()
    record = {col: None for col in RESOLUTION_COLUMNS}
    record.update(resolution_data)
    record["ResolutionID"] = generate_resolution_id()
    record["IncidentID"] = incident_id
    record["CreatedAt"] = now
    record["UpdatedAt"] = now
    resolutions = pd.concat([resolutions, pd.DataFrame([record])], ignore_index=True)
    save_resolutions(resolutions)
    log_activity(incident_id, "Resolution Created")
    return record["ResolutionID"]


def update_resolution(incident_id: str, updates: Dict[str, Any]) -> bool:
    """Update resolution record for an incident."""
    resolutions = get_resolutions()
    mask = resolutions["IncidentID"] == incident_id
    if not mask.any():
        return False
    updates = {k: v for k, v in updates.items() if k not in ("ResolutionID", "IncidentID", "CreatedAt")}
    for k, v in updates.items():
        if k in resolutions.columns:
            resolutions.loc[mask, k] = v
    resolutions.loc[mask, "UpdatedAt"] = datetime.utcnow()
    save_resolutions(resolutions)
    log_activity(incident_id, "Resolution Updated")
    return True

