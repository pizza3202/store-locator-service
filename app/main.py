from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.auth import router as auth_router
from app.api.stores import admin_router as admin_stores_router
from app.api.stores import router as stores_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.base import Base
from app.db.session import engine

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[item.strip() for item in settings.cors_origins.split(",") if item.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "message": "Store Locator Service is running",
        "docs": "/docs",
        "health": "/health",
    }


app.include_router(auth_router)
app.include_router(stores_router)
app.include_router(admin_stores_router)
app.include_router(users_router)
