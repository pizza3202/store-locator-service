from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
    verify_password,
)
from app.db.session import get_db
from app.models.auth import RefreshToken, Role, User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue_tokens(user: User, db: Session) -> TokenResponse:
    role = db.query(Role).filter(Role.id == user.role_id).first()
    token_payload = {"user_id": user.user_id, "email": user.email, "role": role.name}
    access_token = create_access_token(token_payload)
    refresh_token, expires_at = create_refresh_token(token_payload)

    record = RefreshToken(user_id=user.user_id, token_hash=hash_token(refresh_token), expires_at=expires_at)
    db.add(record)
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.is_active.is_(True)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return _issue_tokens(user, db)


@router.post("/token", response_model=TokenResponse)
def login_oauth2(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username, User.is_active.is_(True)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return _issue_tokens(user, db)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash_value = hash_token(payload.refresh_token)
    token_record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash_value, RefreshToken.is_revoked.is_(False))
        .first()
    )
    if not token_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid")

    from app.core.security import decode_token

    decoded = decode_token(payload.refresh_token)
    access_token = create_access_token(
        {"user_id": decoded["user_id"], "email": decoded["email"], "role": decoded["role"]}
    )
    return AccessTokenResponse(access_token=access_token)


@router.post("/logout")
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    token_hash_value = hash_token(payload.refresh_token)
    token_record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash_value).first()
    if token_record:
        token_record.is_revoked = True
        db.commit()
    return {"message": "Logged out"}
