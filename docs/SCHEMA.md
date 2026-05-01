# Database Schema

## Tables

### stores

- `store_id` (PK)
- `name`
- `store_type` (`flagship|regular|outlet|express`)
- `status` (`active|inactive|temporarily_closed`)
- `latitude`, `longitude`
- Address columns: street/city/state/postal_code/country
- `phone`
- Daily hours columns: `hours_mon` ... `hours_sun`
- `created_at`, `updated_at`

### store_services

- `id` (PK)
- `store_id` (FK -> stores.store_id)
- `service_name`
- `created_at`

### users

- `user_id` (PK)
- `email` (unique)
- `password_hash`
- `role_id` (FK -> roles.id)
- `is_active`
- `must_change_password`
- `created_at`, `updated_at`

### roles

- `id` (PK)
- `name` (unique): `admin|marketer|viewer`
- `description`

### permissions

- `id` (PK)
- `code` (unique)
- `description`

### role_permissions

- `id` (PK)
- `role_id` (FK -> roles.id)
- `permission_id` (FK -> permissions.id)
- unique (`role_id`, `permission_id`)

### refresh_tokens

- `id` (PK)
- `user_id` (FK -> users.user_id)
- `token_hash` (unique)
- `expires_at`
- `is_revoked`
- `created_at`

## Indexes

- `idx_stores_lat_lon` on `stores(latitude, longitude)`
- `idx_stores_active_status` partial index where status is active
- `ix_stores_store_type` on `stores(store_type)`
- `ix_stores_address_postal_code` on `stores(address_postal_code)`
- `ix_users_email` on `users(email)`
- `ix_refresh_tokens_token_hash` on `refresh_tokens(token_hash)`
