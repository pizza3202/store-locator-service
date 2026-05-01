import csv
from pathlib import Path

from app.db.session import SessionLocal
from app.models.store import Store, StoreService, StoreStatus, StoreType


def load_csv(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    db = SessionLocal()
    created = 0
    updated = 0
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                store = db.query(Store).filter(Store.store_id == row["store_id"]).first()
                if store:
                    store.name = row["name"]
                    store.store_type = StoreType(row["store_type"])
                    store.status = StoreStatus(row["status"])
                    store.latitude = float(row["latitude"])
                    store.longitude = float(row["longitude"])
                    store.address_street = row["address_street"]
                    store.address_city = row["address_city"]
                    store.address_state = row["address_state"]
                    store.address_postal_code = row["address_postal_code"]
                    store.address_country = row["address_country"]
                    store.phone = row["phone"]
                    store.hours_mon = row["hours_mon"]
                    store.hours_tue = row["hours_tue"]
                    store.hours_wed = row["hours_wed"]
                    store.hours_thu = row["hours_thu"]
                    store.hours_fri = row["hours_fri"]
                    store.hours_sat = row["hours_sat"]
                    store.hours_sun = row["hours_sun"]
                    db.query(StoreService).filter(StoreService.store_id == row["store_id"]).delete()
                    updated += 1
                else:
                    store = Store(
                        store_id=row["store_id"],
                        name=row["name"],
                        store_type=StoreType(row["store_type"]),
                        status=StoreStatus(row["status"]),
                        latitude=float(row["latitude"]),
                        longitude=float(row["longitude"]),
                        address_street=row["address_street"],
                        address_city=row["address_city"],
                        address_state=row["address_state"],
                        address_postal_code=row["address_postal_code"],
                        address_country=row["address_country"],
                        phone=row["phone"],
                        hours_mon=row["hours_mon"],
                        hours_tue=row["hours_tue"],
                        hours_wed=row["hours_wed"],
                        hours_thu=row["hours_thu"],
                        hours_fri=row["hours_fri"],
                        hours_sat=row["hours_sat"],
                        hours_sun=row["hours_sun"],
                    )
                    db.add(store)
                    db.flush()
                    created += 1

                for service_name in row["services"].split("|"):
                    if service_name:
                        db.add(StoreService(store_id=row["store_id"], service_name=service_name))

        db.commit()
        print({"created": created, "updated": updated, "total": created + updated})
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to stores csv")
    args = parser.parse_args()
    load_csv(args.file)
