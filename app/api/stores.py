from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api.dependencies import require_permission
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.store import Store, StoreService, StoreStatus, StoreType
from app.schemas.store import (
    PaginatedStoresResponse,
    StoreCreateRequest,
    StoreCreateWithOptionalCoordinatesRequest,
    StoreResponse,
    StoreSearchRequest,
    StoreSearchResponse,
    StoreSearchResult,
    StoreUpdateRequest,
)
from app.services.geocoding import GeocodingService
from app.utils.distance import bounding_box, distance_miles
from app.utils.hours import is_open_now_for_day, validate_hours

router = APIRouter(tags=["stores"])
geocoding_service = GeocodingService()


def _build_full_address(street: str, city: str, state: str, postal_code: str, country: str) -> str:
    return f"{street}, {city}, {state} {postal_code}, {country}"


def _store_to_response(store: Store) -> StoreResponse:
    return StoreResponse(
        store_id=store.store_id,
        name=store.name,
        store_type=store.store_type,
        status=store.status,
        latitude=store.latitude,
        longitude=store.longitude,
        address_street=store.address_street,
        address_city=store.address_city,
        address_state=store.address_state,
        address_postal_code=store.address_postal_code,
        address_country=store.address_country,
        phone=store.phone,
        services=[svc.service_name for svc in store.services],
        hours_mon=store.hours_mon,
        hours_tue=store.hours_tue,
        hours_wed=store.hours_wed,
        hours_thu=store.hours_thu,
        hours_fri=store.hours_fri,
        hours_sat=store.hours_sat,
        hours_sun=store.hours_sun,
        created_at=store.created_at,
        updated_at=store.updated_at,
    )


@router.post("/api/stores/search", response_model=StoreSearchResponse)
@limiter.limit("10/minute")
@limiter.limit("100/hour")
async def search_stores(request: Request, payload: StoreSearchRequest, db: Session = Depends(get_db)):  # noqa: ARG001
    if payload.address:
        try:
            search_lat, search_lon = await geocoding_service.geocode(payload.address)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Unable to geocode address: {exc}") from exc
    elif payload.postal_code:
        try:
            search_lat, search_lon = await geocoding_service.geocode(f"{payload.postal_code}, USA")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Unable to geocode postal code: {exc}") from exc
    elif payload.latitude is not None and payload.longitude is not None:
        search_lat, search_lon = payload.latitude, payload.longitude
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide address, postal_code, or coordinates")

    min_lat, max_lat, min_lon, max_lon = bounding_box(search_lat, search_lon, payload.radius_miles)
    query = db.query(Store).filter(
        and_(
            Store.latitude >= min_lat,
            Store.latitude <= max_lat,
            Store.longitude >= min_lon,
            Store.longitude <= max_lon,
            Store.status == StoreStatus.active,
        )
    )
    if payload.store_types:
        query = query.filter(Store.store_type.in_(payload.store_types))
    candidates = query.all()

    weekday_map = ["hours_mon", "hours_tue", "hours_wed", "hours_thu", "hours_fri", "hours_sat", "hours_sun"]
    now = datetime.now()
    day_attr = weekday_map[now.weekday()]

    results: list[StoreSearchResult] = []
    for store in candidates:
        service_names = [svc.service_name for svc in store.services]
        if payload.services and not all(required in service_names for required in payload.services):
            continue

        dist = distance_miles(search_lat, search_lon, store.latitude, store.longitude)
        if dist > payload.radius_miles:
            continue

        is_open = is_open_now_for_day(getattr(store, day_attr), now)
        if payload.open_now is True and not is_open:
            continue

        results.append(
            StoreSearchResult(
                store_id=store.store_id,
                name=store.name,
                store_type=store.store_type,
                status=store.status,
                address_street=store.address_street,
                address_city=store.address_city,
                address_state=store.address_state,
                address_postal_code=store.address_postal_code,
                address_country=store.address_country,
                phone=store.phone,
                services=service_names,
                hours_mon=store.hours_mon,
                hours_tue=store.hours_tue,
                hours_wed=store.hours_wed,
                hours_thu=store.hours_thu,
                hours_fri=store.hours_fri,
                hours_sat=store.hours_sat,
                hours_sun=store.hours_sun,
                distance_miles=round(dist, 3),
                is_open_now=is_open,
            )
        )

    results.sort(key=lambda x: x.distance_miles)
    return StoreSearchResponse(
        search_latitude=search_lat,
        search_longitude=search_lon,
        filters={
            "radius_miles": payload.radius_miles,
            "services": payload.services,
            "store_types": payload.store_types,
            "open_now": payload.open_now,
        },
        total=len(results),
        results=results,
    )


admin_router = APIRouter(prefix="/api/admin/stores", tags=["admin-stores"])


@admin_router.post("", response_model=StoreResponse, dependencies=[Depends(require_permission("stores:create"))])
async def create_store(payload: StoreCreateWithOptionalCoordinatesRequest, db: Session = Depends(get_db)):
    if db.query(Store).filter(Store.store_id == payload.store_id).first():
        raise HTTPException(status_code=409, detail="Store already exists")

    for day in ["hours_mon", "hours_tue", "hours_wed", "hours_thu", "hours_fri", "hours_sat", "hours_sun"]:
        if not validate_hours(getattr(payload, day)):
            raise HTTPException(status_code=400, detail=f"Invalid hours value for {day}")

    latitude = payload.latitude
    longitude = payload.longitude
    if latitude is None or longitude is None:
        address = _build_full_address(
            payload.address_street,
            payload.address_city,
            payload.address_state,
            payload.address_postal_code,
            payload.address_country,
        )
        try:
            latitude, longitude = await geocoding_service.geocode(address)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Unable to geocode address: {exc}") from exc

    store_data = payload.model_dump(exclude={"services", "latitude", "longitude"})
    store_data["latitude"] = latitude
    store_data["longitude"] = longitude

    store = Store(**store_data)
    db.add(store)
    db.flush()
    for service_name in payload.services:
        db.add(StoreService(store_id=store.store_id, service_name=service_name))
    db.commit()
    db.refresh(store)
    return _store_to_response(store)


@admin_router.get("", response_model=PaginatedStoresResponse, dependencies=[Depends(require_permission("stores:read"))])
def list_stores(page: int = Query(default=1, ge=1), size: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    total = db.query(func.count(Store.store_id)).scalar() or 0
    stores = db.query(Store).offset((page - 1) * size).limit(size).all()
    return PaginatedStoresResponse(page=page, size=size, total=total, items=[_store_to_response(s) for s in stores])


@admin_router.get("/{store_id}", response_model=StoreResponse, dependencies=[Depends(require_permission("stores:read"))])
def get_store(store_id: str, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.store_id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return _store_to_response(store)


@admin_router.patch("/{store_id}", response_model=StoreResponse, dependencies=[Depends(require_permission("stores:update"))])
def update_store(store_id: str, payload: StoreUpdateRequest, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.store_id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "services" in update_data:
        db.query(StoreService).filter(StoreService.store_id == store_id).delete()
        for service_name in update_data.pop("services"):
            db.add(StoreService(store_id=store_id, service_name=service_name))

    for field, value in update_data.items():
        if field.startswith("hours_") and not validate_hours(value):
            raise HTTPException(status_code=400, detail=f"Invalid hours value for {field}")
        setattr(store, field, value)
    db.commit()
    db.refresh(store)
    return _store_to_response(store)


@admin_router.delete("/{store_id}", dependencies=[Depends(require_permission("stores:delete"))])
def deactivate_store(store_id: str, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.store_id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    store.status = StoreStatus.inactive
    db.commit()
    return {"message": "Store deactivated"}


@admin_router.post("/import", dependencies=[Depends(require_permission("stores:import"))])
async def import_stores(file: UploadFile = File(...), db: Session = Depends(get_db)):
    import csv
    import io

    expected_headers = [
        "store_id",
        "name",
        "store_type",
        "status",
        "latitude",
        "longitude",
        "address_street",
        "address_city",
        "address_state",
        "address_postal_code",
        "address_country",
        "phone",
        "services",
        "hours_mon",
        "hours_tue",
        "hours_wed",
        "hours_thu",
        "hours_fri",
        "hours_sat",
        "hours_sun",
    ]

    content = await file.read()
    text_stream = io.StringIO(content.decode("utf-8"))
    reader = csv.DictReader(text_stream)
    if reader.fieldnames != expected_headers:
        raise HTTPException(status_code=400, detail="CSV headers are invalid")

    failed: list[dict] = []
    valid_payloads: list[StoreCreateRequest] = []

    for index, row in enumerate(reader, start=2):
        try:
            lat_str = (row.get("latitude") or "").strip()
            lon_str = (row.get("longitude") or "").strip()
            if lat_str and lon_str:
                latitude = float(lat_str)
                longitude = float(lon_str)
            else:
                address = _build_full_address(
                    row["address_street"],
                    row["address_city"],
                    row["address_state"],
                    row["address_postal_code"],
                    row["address_country"],
                )
                latitude, longitude = await geocoding_service.geocode(address)

            payload = StoreCreateRequest(
                store_id=row["store_id"],
                name=row["name"],
                store_type=StoreType(row["store_type"]),
                status=StoreStatus(row["status"]),
                latitude=latitude,
                longitude=longitude,
                address_street=row["address_street"],
                address_city=row["address_city"],
                address_state=row["address_state"],
                address_postal_code=row["address_postal_code"],
                address_country=row["address_country"],
                phone=row["phone"],
                services=[item for item in row["services"].split("|") if item],
                hours_mon=row["hours_mon"],
                hours_tue=row["hours_tue"],
                hours_wed=row["hours_wed"],
                hours_thu=row["hours_thu"],
                hours_fri=row["hours_fri"],
                hours_sat=row["hours_sat"],
                hours_sun=row["hours_sun"],
            )
            valid_payloads.append(payload)
        except Exception as exc:  # noqa: BLE001
            failed.append({"row": index, "error": str(exc)})

    if failed:
        db.rollback()
        return {
            "total_rows": len(valid_payloads) + len(failed),
            "created": 0,
            "updated": 0,
            "failed": failed,
            "message": "Import rolled back due to errors",
        }

    created = 0
    updated = 0
    for payload in valid_payloads:
        store = db.query(Store).filter(Store.store_id == payload.store_id).first()
        if store:
            for key, value in payload.model_dump(exclude={"store_id", "services"}).items():
                setattr(store, key, value)
            db.query(StoreService).filter(StoreService.store_id == payload.store_id).delete()
            for svc in payload.services:
                db.add(StoreService(store_id=payload.store_id, service_name=svc))
            updated += 1
        else:
            store = Store(**payload.model_dump(exclude={"services"}))
            db.add(store)
            db.flush()
            for svc in payload.services:
                db.add(StoreService(store_id=payload.store_id, service_name=svc))
            created += 1
    db.commit()

    return {
        "total_rows": len(valid_payloads),
        "created": created,
        "updated": updated,
        "failed": [],
    }
