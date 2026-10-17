from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Optional

IST_TIMEZONE_STR = "Asia/Kolkata"
IST = ZoneInfo(IST_TIMEZONE_STR)


def get_current_ist_time() -> datetime:
    """Return the current datetime in Indian Standard Time (IST)."""
    return datetime.now(IST)


def normalize_to_ist(dt: datetime) -> datetime:
    """
    Ensure an incoming datetime (from API request) is converted to IST.
    - If naive (no tzinfo), treat as local studio time (IST, Asia/Kolkata).
    - If already timezone-aware, convert using .astimezone(IST).
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=IST)
    return dt.astimezone(IST)


def ensure_ist_aware(dt: datetime) -> datetime:
    """
    Ensure a datetime retrieved from database (where all times are stored in IST)
    has the IST tzinfo attached.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=IST)
    return dt.astimezone(IST)


def convert_to_timezone(dt: datetime, target_tz_name: Optional[str] = None) -> datetime:
    """
    Convert an existing datetime (stored in IST) to a target timezone.
    If target_tz_name is empty or None, returns the datetime in IST.
    Raises ValueError if target_tz_name is invalid.
    """
    dt_ist = ensure_ist_aware(dt)

    if not target_tz_name or target_tz_name.strip() == "":
        return dt_ist
    
    clean_tz = target_tz_name.strip()
    try:
        target_tz = ZoneInfo(clean_tz)
    except (ZoneInfoNotFoundError, KeyError) as e:
        raise ValueError(f"Unknown timezone identifier: '{target_tz_name}'") from e

    return dt_ist.astimezone(target_tz)
