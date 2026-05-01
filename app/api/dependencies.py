from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.auth import Permission, RolePermission, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.query(User).filter(User.user_id == payload.get("user_id"), User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_permission(permission_code: str):
    def checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        permission = db.query(Permission).filter(Permission.code == permission_code).first()
        if not permission:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission not configured")

        role_permission = (
            db.query(RolePermission)
            .filter(RolePermission.role_id == current_user.role_id, RolePermission.permission_id == permission.id)
            .first()
        )
        if not role_permission:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return checker
