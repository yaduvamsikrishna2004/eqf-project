from pathlib import Path

# Path to Excel file (Windows path using backslashes). Keep configurable.
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default Excel file location
EXCEL_FILE = DATA_DIR / "EFQ_Dashboard.xlsx"

# Sheet names
INCIDENTS_SHEET = "incidents"
RESOLUTIONS_SHEET = "resolutions"
ACTIVITIES_SHEET = "activities"

# ID formats
INCIDENT_ID_PREFIX = "EFQ-"
RESOLUTION_ID_PREFIX = "RES-"
ACTIVITY_ID_PREFIX = "ACT-"

# Mandatory fields for incident creation
MANDATORY_FIELDS = [
    "OEM",
    "CustomerComplaint",
    "Custodian",
    "Severity",
    "IssueType",
]

# Roles
ROLES = ["Reporter", "Custodian", "Management"]

# Custodians list (can be extended)
CUSTODIANS = ["Engineer A", "Engineer B", "Engineer C", "Engineer D"]

# Investigation statuses
INVESTIGATION_STATUSES = ["New", "Investigation Started", "Root Cause Identified", "Action In Progress", "Validation", "Closed"]