from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, Float, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StoreType(str, Enum):
    flagship = "flagship"
    regular = "regular"
    outlet = "outlet"
    express = "express"


class StoreStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    temporarily_closed = "temporarily_closed"


class Store(Base):
    __tablename__ = "stores"

    store_id: Mapped[str] = mapped_column(String(10), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    store_type: Mapped[StoreType] = mapped_column(SQLEnum(StoreType), nullable=False, index=True)
    status: Mapped[StoreStatus] = mapped_column(SQLEnum(StoreStatus), nullable=False, default=StoreStatus.active)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address_street: Mapped[str] = mapped_column(String(255), nullable=False)
    address_city: Mapped[str] = mapped_column(String(100), nullable=False)
    address_state: Mapped[str] = mapped_column(String(2), nullable=False)
    address_postal_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    address_country: Mapped[str] = mapped_column(String(3), nullable=False, default="USA")
    phone: Mapped[str] = mapped_column(String(12), nullable=False)
    hours_mon: Mapped[str] = mapped_column(String(20), nullable=False)
    hours_tue: Mapped[str] = mapped_column(String(20), nullable=False)
    hours_wed: Mapped[str] = mapped_column(String(20), nullable=False)
    hours_thu: Mapped[str] = mapped_column(String(20), nullable=False)
    hours_fri: Mapped[str] = mapped_column(String(20), nullable=False)
    hours_sat: Mapped[str] = mapped_column(String(20), nullable=False)
    hours_sun: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    services: Mapped[list["StoreService"]] = relationship("StoreService", back_populates="store", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_stores_lat_lon", "latitude", "longitude"),
        Index("idx_stores_active_status", "status", postgresql_where=text("status = 'active'")),
    )


class StoreService(Base):
    __tablename__ = "store_services"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.store_id", ondelete="CASCADE"), index=True)
    service_name: Mapped[str] = mapped_column(String(50), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    store: Mapped[Store] = relationship("Store", back_populates="services")
