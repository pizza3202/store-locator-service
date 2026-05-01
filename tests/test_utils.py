from app.core.security import hash_password, verify_password
from app.utils.distance import bounding_box, distance_miles
from app.utils.hours import is_open_now_for_day, validate_hours


def test_bounding_box():
    min_lat, max_lat, min_lon, max_lon = bounding_box(42.3601, -71.0589, 10)
    assert min_lat < max_lat
    assert min_lon < max_lon


def test_distance():
    dist = distance_miles(42.3601, -71.0589, 42.3555, -71.0602)
    assert dist >= 0
    assert dist < 2


def test_hours_validation():
    assert validate_hours("08:00-22:00")
    assert validate_hours("closed")
    assert not validate_hours("25:00-26:00")
    assert not validate_hours("22:00-08:00")


def test_is_open_now():
    from datetime import datetime

    now = datetime.strptime("2026-04-30 12:00", "%Y-%m-%d %H:%M")
    assert is_open_now_for_day("08:00-22:00", now)
    assert not is_open_now_for_day("closed", now)


def test_password_hashing():
    password = "TestPassword123!"
    password_hash = hash_password(password)
    assert password_hash != password
    assert verify_password(password, password_hash)
