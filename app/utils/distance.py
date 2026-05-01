import math

from geopy.distance import geodesic


def bounding_box(latitude: float, longitude: float, radius_miles: float) -> tuple[float, float, float, float]:
    lat_delta = radius_miles / 69.0
    lon_delta = radius_miles / (69.0 * math.cos(math.radians(latitude)))
    return (
        latitude - lat_delta,
        latitude + lat_delta,
        longitude - lon_delta,
        longitude + lon_delta,
    )


def distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return geodesic((lat1, lon1), (lat2, lon2)).miles
