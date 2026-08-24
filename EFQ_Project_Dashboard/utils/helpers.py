from datetime import datetime


def now_utc_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def format_datetime(dt) -> str:
    if dt is None:
        return ""
    try:
        return pd.to_datetime(dt).isoformat()
    except Exception:
        return str(dt)
