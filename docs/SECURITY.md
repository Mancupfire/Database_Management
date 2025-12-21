# MoneyMinder Security Notes

## Database Roles and Privileges
- `moneyminder_admin` (localhost): full privileges on `MoneyMinder_DB` (for migrations/ops).
- `moneyminder_app` (localhost): `SELECT, INSERT, UPDATE, DELETE, EXECUTE` only (used by the backend).
- `moneyminder_readonly` (localhost): `SELECT` only (analytics/reporting).
- Passwords are defined in `Physical_Schema_Definition.sql` (currently `MM_Admin@2024!r3set`, `MM_App@2024!r3set`, `MM_Read@2024!r3set`); **override them before production**, rerun grants, and update backend `.env`.

## Encryption at Rest (MySQL AES)
- `Users.password_hash_enc` stores an AES-encrypted copy of the bcrypt hash.
- Helper function: `FN_Get_Encryption_Key()` returns the AES key (derived from a seed string). **Change the seed** (`MoneyMinder-Encryption-Key-ChangeMe`) before production, then re-run the schema or update the function:
  ```sql
  DROP FUNCTION IF EXISTS FN_Get_Encryption_Key;
  CREATE FUNCTION FN_Get_Encryption_Key()
  RETURNS VARBINARY(32)
  DETERMINISTIC
  RETURN SHA2('your-new-secret-seed', 256);
  ```
- Triggers:
  - `TRG_Users_Encrypt_Insert` encrypts `password_hash` on insert.
  - `TRG_Users_Encrypt_Update` re-encrypts when the hash changes.
- View for audit/ops: `View_Users_Secure` shows decrypted hashes (still bcrypt hashes) for controlled use.

## Application Secrets
- Backend secrets read from `.env` (see `backend/.env.example`):
  - `SECRET_KEY`, `JWT_SECRET_KEY`
  - `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_NAME`
- Rotate these for every deployment; do not leave defaults in production.

## Hardening Tips
- Restrict MySQL users to least privilege and limit host access (currently `localhost`).
- Enforce SSL on MySQL connections in production.
- Rotate AES seed and MySQL user passwords regularly; document the rotation time.
- Keep `setup.sh` away from production or add a confirmation prompt (it drops/recreates the DB).
- Use prepared statements (already used in backend) to prevent SQL injection.
- Lock down CORS: set `FRONTEND_ORIGINS` in `.env` (comma-separated origins, e.g., `http://localhost:8080,https://demo.example.com`); backend now defaults to `http://localhost:8080`.

## Quick Validation
After loading schema/data:
```sql
-- Verify encryption columns populated
SELECT user_id, LENGTH(password_hash_enc) AS enc_len FROM Users;

-- Verify decrypted view works
SELECT user_id, password_hash_decrypted FROM View_Users_Secure LIMIT 5;
```
