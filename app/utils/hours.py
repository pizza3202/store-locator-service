from datetime import datetime


def validate_hours(value: str) -> bool:
    if value == "closed":
        return True
    if len(value) != 11 or "-" not in value:
        return False
    start, end = value.split("-")
    try:
        start_dt = datetime.strptime(start, "%H:%M")
        end_dt = datetime.strptime(end, "%H:%M")
    except ValueError:
        return False
    return start_dt < end_dt


def is_open_now_for_day(value: str, now: datetime) -> bool:
    if value == "closed":
        return False
    start, end = value.split("-")
    start_t = datetime.strptime(start, "%H:%M").time()
    end_t = datetime.strptime(end, "%H:%M").time()
    return start_t <= now.time() <= end_t
