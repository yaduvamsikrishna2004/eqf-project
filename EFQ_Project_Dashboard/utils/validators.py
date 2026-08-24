from typing import Dict, List
from config.config import MANDATORY_FIELDS


def validate_incident_payload(payload: Dict[str, object]) -> List[str]:
    """Return list of missing mandatory fields. Empty list means valid."""
    missing = []
    for field in MANDATORY_FIELDS:
        val = payload.get(field)
        if val is None:
            missing.append(field)
        else:
            # empty string check
            if isinstance(val, str) and val.strip() == "":
                missing.append(field)
    return missing
