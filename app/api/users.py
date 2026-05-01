from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import require_permission
from app.core.security import hash_password
from app.db.session import get_db
from app.models.auth import Role, User
from app.schemas.auth import UserCreateRequest, UserResponse, UserUpdateRequest

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


def _serialize_user(user: User, role_name: str) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        role=role_name,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        created_at=user.created_at,
    )


@router.post("", response_model=UserResponse, dependencies=[Depends(require_permission("users:create"))])
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.name == payload.role).first()
    if not role:
        raise HTTPException(status_code=400, detail="Role not found")
    if db.query(User).filter(User.user_id == payload.user_id).first():
        raise HTTPException(status_code=409, detail="User exists")

    user = User(
        user_id=payload.user_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role_id=role.id,
        is_active=True,
        must_change_password=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _serialize_user(user, role.name)


@router.get("", response_model=list[UserResponse], dependencies=[Depends(require_permission("users:read"))])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    role_map = {r.id: r.name for r in db.query(Role).all()}
    return [_serialize_user(u, role_map.get(u.role_id, "unknown")) for u in users]


@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_permission("users:update"))])
def update_user(user_id: str, payload: UserUpdateRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.role:
        role = db.query(Role).filter(Role.name == payload.role).first()
        if not role:
            raise HTTPException(status_code=400, detail="Role not found")
        user.role_id = role.id

    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return _serialize_user(user, role.name)


@router.delete("/{user_id}", dependencies=[Depends(require_permission("users:delete"))])
def deactivate_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"message": "User deactivated"}
