from datetime import datetime


def _parse_minutes(value: str, allow_24: bool = False) -> int:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("Invalid time format")
    hour = int(parts[0])
    minute = int(parts[1])
    if minute < 0 or minute > 59:
        raise ValueError("Invalid minute")
    if hour == 24 and minute == 0 and allow_24:
        return 24 * 60
    if hour < 0 or hour > 23:
        raise ValueError("Invalid hour")
    return hour * 60 + minute


def validate_hours(value: str) -> bool:
    if value == "closed":
        return True
    if len(value) != 11 or "-" not in value:
        return False
    start, end = value.split("-")
    try:
        start_min = _parse_minutes(start, allow_24=False)
        end_min = _parse_minutes(end, allow_24=True)
    except ValueError:
        return False
    return start_min < end_min


def is_open_now_for_day(value: str, now: datetime) -> bool:
    if value == "closed":
        return False
    if "-" not in value:
        return False
    start, end = value.split("-")
    try:
        start_min = _parse_minutes(start, allow_24=False)
        end_min = _parse_minutes(end, allow_24=True)
    except ValueError:
        return False
    now_min = now.hour * 60 + now.minute
    return start_min <= now_min <= end_min
