# MoneyMinder Test Plan

## Scope
- Backend API: auth, accounts, analytics (including window-function trends), health.
- Frontend UI: static assets and main page availability.
- Performance: EXPLAIN ANALYZE capture for key queries.
- Load: synthetic insert simulation for Transactions.
- Integration: stored procedures, budget/unusual analytics endpoints, recurring worker sanity.

## Test Types
- Automated smoke (backend): `./venv/bin/pytest -q` (requires MySQL and sample data).
- Backend integrations: `./venv/bin/pytest backend/tests/test_integrations.py` (budget status, unusual spending view, recurring stored proc).
- UI smoke (frontend): `./scripts/ui_smoke.sh` against running frontend.
- Performance evidence: `./scripts/run_explain.sh` to generate `docs/perf_results.txt`.
- Load simulation: `N=100 ./scripts/load_sim.sh` to insert synthetic transactions.
- API smoke collection (Postman): import `scripts/postman_collection.json`, set `baseUrl`/`token`, run collection.
- UI/API regression (Cypress skeleton): see `scripts/cypress_smoke.cy.js` (requires Cypress, front/back running).

## Environment Setup
1) MySQL running; load schema/data:
```bash
mysql -u root -p < Physical_Schema_Definition.sql
mysql -u root -p < Sample_Data.sql
```
2) Backend venv:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
3) Start app (for UI tests): `./run.sh` from repo root.

## Execution Steps
- Backend smoke: `cd backend && source venv/bin/activate && ./venv/bin/pytest -q`
- UI smoke: `BASE_URL=http://localhost:8080 ./scripts/ui_smoke.sh`
- Performance: `MYSQL_USER=root MYSQL_PASSWORD=... MYSQL_DB=MoneyMinder_DB ./scripts/run_explain.sh`
- Load sim: `MYSQL_USER=root MYSQL_PASSWORD=... MYSQL_DB=MoneyMinder_DB N=500 ./scripts/load_sim.sh`
- Cypress (optional): `BASE_URL=http://localhost:8080 BACKEND_URL=http://localhost:5000 npx cypress run --spec scripts/cypress_smoke.cy.js`

## Expected Results
- Smoke tests: all pass (admin ping passes with sample admin user `john.doe@example.com` / `Demo@2024`).
- Integration tests: budget/unusual endpoints return data; recurring stored procedure inserts a new transaction and advances due date (cleanup handled in-test).
- UI smoke: returns 200 and finds expected markers in HTML/CSS/JS.
- Performance: `docs/perf_results.txt` captured for reporting.
- Load sim: Inserts specified rows; counts increase accordingly.
