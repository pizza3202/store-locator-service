from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.auth import Permission, Role, RolePermission, User

ROLE_PERMISSIONS = {
    "admin": [
        "stores:create",
        "stores:read",
        "stores:update",
        "stores:delete",
        "stores:import",
        "users:create",
        "users:read",
        "users:update",
        "users:delete",
    ],
    "marketer": ["stores:create", "stores:read", "stores:update", "stores:delete", "stores:import"],
    "viewer": ["stores:read"],
}


def run():
    db = SessionLocal()
    try:
        role_map: dict[str, Role] = {}
        for role_name in ROLE_PERMISSIONS:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name, description=f"{role_name} role")
                db.add(role)
                db.flush()
            role_map[role_name] = role

        permission_map: dict[str, Permission] = {}
        for codes in ROLE_PERMISSIONS.values():
            for code in codes:
                if code in permission_map:
                    continue
                permission = db.query(Permission).filter(Permission.code == code).first()
                if not permission:
                    permission = Permission(code=code, description=code)
                    db.add(permission)
                    db.flush()
                permission_map[code] = permission

        for role_name, codes in ROLE_PERMISSIONS.items():
            role = role_map[role_name]
            for code in codes:
                permission = permission_map[code]
                exists = (
                    db.query(RolePermission)
                    .filter(RolePermission.role_id == role.id, RolePermission.permission_id == permission.id)
                    .first()
                )
                if not exists:
                    db.add(RolePermission(role_id=role.id, permission_id=permission.id))

        users = [
            ("U001", "admin@test.com", "admin"),
            ("U002", "marketer@test.com", "marketer"),
            ("U003", "viewer@test.com", "viewer"),
        ]
        for user_id, email, role_name in users:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                user = User(
                    user_id=user_id,
                    email=email,
                    password_hash=hash_password("TestPassword123!"),
                    role_id=role_map[role_name].id,
                    is_active=True,
                    must_change_password=True,
                )
                db.add(user)
            else:
                # Keep seeded users deterministic so login always works in local/dev.
                user.email = email
                user.password_hash = hash_password("TestPassword123!")
                user.role_id = role_map[role_name].id
                user.is_active = True
                user.must_change_password = True
        db.commit()
        print("Seed completed")
    finally:
        db.close()


if __name__ == "__main__":
    run()
