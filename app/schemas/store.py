from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.store import StoreStatus, StoreType

ALLOWED_SERVICES = {
    "pharmacy",
    "pickup",
    "returns",
    "optical",
    "photo_printing",
    "gift_wrapping",
    "automotive",
    "garden_center",
}


class StoreBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    store_type: StoreType
    status: StoreStatus = StoreStatus.active
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address_street: str
    address_city: str
    address_state: str = Field(min_length=2, max_length=2)
    address_postal_code: str = Field(min_length=5, max_length=5)
    address_country: str = Field(min_length=3, max_length=3, default="USA")
    phone: str = Field(pattern=r"^\d{3}-\d{3}-\d{4}$")
    services: list[str]
    hours_mon: str
    hours_tue: str
    hours_wed: str
    hours_thu: str
    hours_fri: str
    hours_sat: str
    hours_sun: str

    @field_validator("services")
    @classmethod
    def validate_services(cls, value: list[str]) -> list[str]:
        invalid = [item for item in value if item not in ALLOWED_SERVICES]
        if invalid:
            raise ValueError(f"Invalid services: {invalid}")
        return value


class StoreCreateRequest(StoreBase):
    store_id: str = Field(pattern=r"^S\d{4}$")


class StoreCreateWithOptionalCoordinatesRequest(BaseModel):
    store_id: str = Field(pattern=r"^S\d{4}$")
    name: str = Field(min_length=1, max_length=255)
    store_type: StoreType
    status: StoreStatus = StoreStatus.active
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    address_street: str
    address_city: str
    address_state: str = Field(min_length=2, max_length=2)
    address_postal_code: str = Field(min_length=5, max_length=5)
    address_country: str = Field(min_length=3, max_length=3, default="USA")
    phone: str = Field(pattern=r"^\d{3}-\d{3}-\d{4}$")
    services: list[str]
    hours_mon: str
    hours_tue: str
    hours_wed: str
    hours_thu: str
    hours_fri: str
    hours_sat: str
    hours_sun: str

    @field_validator("services")
    @classmethod
    def validate_services(cls, value: list[str]) -> list[str]:
        invalid = [item for item in value if item not in ALLOWED_SERVICES]
        if invalid:
            raise ValueError(f"Invalid services: {invalid}")
        return value


class StoreUpdateRequest(BaseModel):
    name: str | None = None
    phone: str | None = Field(default=None, pattern=r"^\d{3}-\d{3}-\d{4}$")
    services: list[str] | None = None
    status: StoreStatus | None = None
    hours_mon: str | None = None
    hours_tue: str | None = None
    hours_wed: str | None = None
    hours_thu: str | None = None
    hours_fri: str | None = None
    hours_sat: str | None = None
    hours_sun: str | None = None

    @field_validator("services")
    @classmethod
    def validate_services(cls, value):
        if value is None:
            return value
        invalid = [item for item in value if item not in ALLOWED_SERVICES]
        if invalid:
            raise ValueError(f"Invalid services: {invalid}")
        return value


class StoreResponse(StoreBase):
    store_id: str
    created_at: datetime
    updated_at: datetime


class PaginatedStoresResponse(BaseModel):
    page: int
    size: int
    total: int
    items: list[StoreResponse]


class StoreSearchRequest(BaseModel):
    address: str | None = None
    postal_code: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    radius_miles: float = Field(default=10, ge=0.1, le=100)
    services: list[str] = Field(default_factory=list)
    store_types: list[StoreType] = Field(default_factory=list)
    open_now: bool | None = None


class StoreSearchResult(BaseModel):
    store_id: str
    name: str
    store_type: StoreType
    status: StoreStatus
    address_street: str
    address_city: str
    address_state: str
    address_postal_code: str
    address_country: str
    phone: str
    services: list[str]
    hours_mon: str
    hours_tue: str
    hours_wed: str
    hours_thu: str
    hours_fri: str
    hours_sat: str
    hours_sun: str
    distance_miles: float
    is_open_now: bool


class StoreSearchResponse(BaseModel):
    search_latitude: float
    search_longitude: float
    filters: dict
    total: int
    results: list[StoreSearchResult]
