from typing import Any

import httpx
import redis
from redis.exceptions import RedisError

from app.core.config import get_settings

settings = get_settings()


class GeocodingService:
    def __init__(self):
        self.memory_cache: dict[str, str] = {}
        try:
            self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            self.redis_client.ping()
        except RedisError:
            self.redis_client = None

    def _cache_key(self, query: str) -> str:
        return f"geocode:{query.strip().lower()}"

    async def geocode(self, query: str) -> tuple[float, float]:
        key = self._cache_key(query)
        cached = self.redis_client.get(key) if self.redis_client else self.memory_cache.get(key)
        if cached:
            lat, lon = cached.split(",")
            return float(lat), float(lon)

        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": query, "format": "json", "limit": 1}
        headers = {"User-Agent": "store-locator-app"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data: list[dict[str, Any]] = response.json()
        except httpx.HTTPStatusError as exc:
            raise ValueError(f"Geocoding provider returned HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise ValueError("Geocoding provider request failed") from exc

        if not data:
            raise ValueError("Location not found")

        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        value = f"{lat},{lon}"
        if self.redis_client:
            self.redis_client.setex(key, 30 * 24 * 60 * 60, value)
        else:
            self.memory_cache[key] = value
        return lat, lon
