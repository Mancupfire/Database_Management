# MoneyMinder Testing Guide

## Prerequisites
- MySQL running with `MoneyMinder_DB` loaded:
  ```bash
  mysql -u root -p < Physical_Schema_Definition.sql
  mysql -u root -p < Sample_Data.sql
  ```
- Python venv active (`backend/venv`) and dependencies installed:
  ```bash
  pip install -r requirements.txt
  ```

## Test Suites
- `backend/tests/test_smoke.py` (pytest)
  - Checks DB connectivity (`Database.test_connection`)
  - Health endpoint (`/api/health`)
  - Auth + accounts CRUD (login, list, create/delete)
  - Analytics window-function endpoint (`/api/analytics/monthly-trends`)

## Running Tests
From `backend/`:
```bash
source venv/bin/activate
pytest -q
```

## Notes
- Tests assume the sample data (demo users) is loaded so `john.doe@example.com` / `Demo@2024` works.
- Tests mutate data (create/delete an account) but clean up after themselves.
- For isolated CI, point `DB_HOST/DB_USER/DB_PASSWORD/DB_NAME` to a disposable test database via environment variables. 
