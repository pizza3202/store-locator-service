import io

from fastapi.testclient import TestClient

from app.main import app
from app.models.store import Store, StoreService, StoreStatus, StoreType
from app.db.session import SessionLocal
from scripts.seed_data import run as seed_run


def _ensure_sample_store():
    db = SessionLocal()
    try:
        store = db.query(Store).filter(Store.store_id == "S9000").first()
        if store:
            return
        store = Store(
            store_id="S9000",
            name="Boston Test Store",
            store_type=StoreType.regular,
            status=StoreStatus.active,
            latitude=42.3601,
            longitude=-71.0589,
            address_street="1 Test St",
            address_city="Boston",
            address_state="MA",
            address_postal_code="02101",
            address_country="USA",
            phone="617-555-0100",
            hours_mon="08:00-22:00",
            hours_tue="08:00-22:00",
            hours_wed="08:00-22:00",
            hours_thu="08:00-22:00",
            hours_fri="08:00-22:00",
            hours_sat="08:00-22:00",
            hours_sun="08:00-22:00",
        )
        db.add(store)
        db.flush()
        db.add(StoreService(store_id=store.store_id, service_name="pickup"))
        db.commit()
    finally:
        db.close()


def _login(client: TestClient, email: str, password: str):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()


def test_auth_flow_and_search():
    seed_run()
    _ensure_sample_store()

    client = TestClient(app)

    tokens = _login(client, "admin@test.com", "TestPassword123!")
    refresh = tokens["refresh_token"]

    refresh_res = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()

    search_res = client.post(
        "/api/stores/search",
        json={
            "latitude": 42.3601,
            "longitude": -71.0589,
            "radius_miles": 10,
            "services": ["pickup"],
            "store_types": ["regular"],
            "open_now": False,
        },
    )
    assert search_res.status_code == 200
    assert search_res.json()["total"] >= 1

    logout_res = client.post("/api/auth/logout", json={"refresh_token": refresh})
    assert logout_res.status_code == 200


def test_rbac_viewer_cannot_create_store():
    seed_run()
    client = TestClient(app)
    tokens = _login(client, "viewer@test.com", "TestPassword123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create_res = client.post(
        "/api/admin/stores",
        headers=headers,
        json={
            "store_id": "S9999",
            "name": "Unauthorized Test Store",
            "store_type": "regular",
            "status": "active",
            "latitude": 42.0,
            "longitude": -71.0,
            "address_street": "123 Test",
            "address_city": "Boston",
            "address_state": "MA",
            "address_postal_code": "02101",
            "address_country": "USA",
            "phone": "617-555-9999",
            "services": ["pickup"],
            "hours_mon": "08:00-20:00",
            "hours_tue": "08:00-20:00",
            "hours_wed": "08:00-20:00",
            "hours_thu": "08:00-20:00",
            "hours_fri": "08:00-20:00",
            "hours_sat": "08:00-20:00",
            "hours_sun": "08:00-20:00",
        },
    )
    assert create_res.status_code == 403


def test_admin_store_list_has_pagination_shape():
    seed_run()
    client = TestClient(app)
    tokens = _login(client, "admin@test.com", "TestPassword123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    res = client.get("/api/admin/stores?page=1&size=5", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert {"page", "size", "total", "items"}.issubset(body.keys())
    assert body["page"] == 1
    assert body["size"] == 5
    assert isinstance(body["items"], list)


def test_create_store_auto_geocodes_when_coordinates_missing():
    seed_run()
    client = TestClient(app)
    tokens = _login(client, "admin@test.com", "TestPassword123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    store_id = "S9888"

    db = SessionLocal()
    try:
        existing = db.query(Store).filter(Store.store_id == store_id).first()
        if existing:
            db.delete(existing)
            db.commit()
    finally:
        db.close()

    from app.api import stores as stores_module

    async def fake_geocode(_query: str):
        return 42.3611, -71.0570

    stores_module.geocoding_service.geocode = fake_geocode

    create_res = client.post(
        "/api/admin/stores",
        headers=headers,
        json={
            "store_id": store_id,
            "name": "Geocoded Store",
            "store_type": "regular",
            "status": "active",
            "address_street": "99 Demo St",
            "address_city": "Boston",
            "address_state": "MA",
            "address_postal_code": "02101",
            "address_country": "USA",
            "phone": "617-555-9888",
            "services": ["pickup"],
            "hours_mon": "08:00-20:00",
            "hours_tue": "08:00-20:00",
            "hours_wed": "08:00-20:00",
            "hours_thu": "08:00-20:00",
            "hours_fri": "08:00-20:00",
            "hours_sat": "08:00-20:00",
            "hours_sun": "08:00-20:00",
        },
    )
    assert create_res.status_code == 200
    body = create_res.json()
    assert body["latitude"] == 42.3611
    assert body["longitude"] == -71.057


def _headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def _delete_store_if_exists(store_id: str) -> None:
    db = SessionLocal()
    try:
        store = db.query(Store).filter(Store.store_id == store_id).first()
        if store:
            db.delete(store)
            db.commit()
    finally:
        db.close()


def _ensure_store(
    store_id: str,
    lat: float,
    lon: float,
    services: list[str],
    store_type: StoreType = StoreType.regular,
    status: StoreStatus = StoreStatus.active,
) -> None:
    db = SessionLocal()
    try:
        existing = db.query(Store).filter(Store.store_id == store_id).first()
        if existing:
            db.delete(existing)
            db.commit()

        store = Store(
            store_id=store_id,
            name=f"Store {store_id}",
            store_type=store_type,
            status=status,
            latitude=lat,
            longitude=lon,
            address_street="1 Main St",
            address_city="Boston",
            address_state="MA",
            address_postal_code="02101",
            address_country="USA",
            phone="617-555-0100",
            hours_mon="08:00-22:00",
            hours_tue="08:00-22:00",
            hours_wed="08:00-22:00",
            hours_thu="08:00-22:00",
            hours_fri="08:00-22:00",
            hours_sat="08:00-22:00",
            hours_sun="08:00-22:00",
        )
        db.add(store)
        db.flush()
        for svc in services:
            db.add(StoreService(store_id=store_id, service_name=svc))
        db.commit()
    finally:
        db.close()


def test_search_by_address_with_geocoding_mock():
    seed_run()
    client = TestClient(app)
    _ensure_store("S9702", 42.3601, -71.0589, ["pickup"])

    from app.api import stores as stores_module

    async def fake_geocode(_query: str):
        return 42.3601, -71.0589

    stores_module.geocoding_service.geocode = fake_geocode
    response = client.post("/api/stores/search", json={"address": "1 Main St, Boston, MA"})
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_search_by_zip_with_geocoding_mock():
    seed_run()
    client = TestClient(app)
    _ensure_store("S9703", 42.3601, -71.0589, ["pickup"])

    from app.api import stores as stores_module

    async def fake_geocode(_query: str):
        return 42.3601, -71.0589

    stores_module.geocoding_service.geocode = fake_geocode
    response = client.post("/api/stores/search", json={"postal_code": "02101"})
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_csv_import_validation_failure():
    seed_run()
    client = TestClient(app)
    admin_tokens = _login(client, "admin@test.com", "TestPassword123!")
    admin_headers = _headers(admin_tokens["access_token"])
    content = "bad,header\n1,2\n"
    files = {"file": ("bad.csv", content, "text/csv")}
    response = client.post("/api/admin/stores/import", headers=admin_headers, files=files)
    assert response.status_code == 400


def test_logout_revokes_refresh_token():
    seed_run()
    client = TestClient(app)
    tokens = _login(client, "admin@test.com", "TestPassword123!")
    refresh_token = tokens["refresh_token"]

    logout = client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 200

    refresh_again = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_again.status_code == 401


def test_integration_csv_import_with_geocoding():
    seed_run()
    client = TestClient(app)
    admin_headers = _headers(_login(client, "admin@test.com", "TestPassword123!")["access_token"])
    store_id = "S9712"
    _delete_store_if_exists(store_id)

    from app.api import stores as stores_module

    async def fake_geocode(_query: str):
        return 42.3611, -71.0570

    stores_module.geocoding_service.geocode = fake_geocode

    header = (
        "store_id,name,store_type,status,latitude,longitude,address_street,address_city,address_state,"
        "address_postal_code,address_country,phone,services,hours_mon,hours_tue,hours_wed,hours_thu,hours_fri,"
        "hours_sat,hours_sun\n"
    )
    row = (
        f"{store_id},Import Geocode Store,regular,active,,,1 Import St,Boston,MA,02101,USA,617-555-0112,pickup|pharmacy,"
        "08:00-20:00,08:00-20:00,08:00-20:00,08:00-20:00,08:00-20:00,08:00-20:00,08:00-20:00\n"
    )
    files = {"file": ("import.csv", io.StringIO(header + row).getvalue(), "text/csv")}
    response = client.post("/api/admin/stores/import", headers=admin_headers, files=files)
    assert response.status_code == 200
    assert response.json()["created"] >= 1
