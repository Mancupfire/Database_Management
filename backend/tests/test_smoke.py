import os
import sys
import json
from pathlib import Path
import pytest
import pymysql

# Ensure backend package is on path when running pytest from backend/
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from config import Config
from database import Database


@pytest.fixture(scope="session", autouse=True)
def ensure_env():
    # Ensure we point to test DB if provided
    os.environ.setdefault("FLASK_ENV", "development")
    yield


@pytest.fixture(scope="session")
def app():
    app = create_app("development")
    app.config["TESTING"] = True
    return app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def db_available():
    ok = Database.test_connection()
    if not ok:
        pytest.skip("Database not reachable on configured host; skipping API smoke tests.")
    return True


def test_db_connection():
    ok = Database.test_connection()
    if not ok:
        pytest.skip("Database not reachable on configured host.")
    assert ok is True


def test_health(client, db_available):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def login(client, email="john.doe@example.com", password="Demo@2024"):
    resp = client.post(
        "/api/auth/login",
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    return data["token"], data["user"]["user_id"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_accounts_flow(client, db_available):
    token, user_id = login(client)

    # List accounts
    resp = client.get("/api/accounts/", headers=auth_headers(token))
    assert resp.status_code == 200
    accounts = resp.get_json().get("accounts", [])
    assert isinstance(accounts, list)

    # Create then delete an account (isolated)
    resp = client.post(
        "/api/accounts/",
        headers=auth_headers(token),
        data=json.dumps(
            {
                "account_name": "Test Account",
                "account_type": "Cash",
                "balance": 123.45,
            }
        ),
        content_type="application/json",
    )
    assert resp.status_code == 201
    new_id = resp.get_json().get("account_id")
    assert new_id

    resp = client.delete(f"/api/accounts/{new_id}", headers=auth_headers(token))
    assert resp.status_code == 200


def test_analytics_trends(client, db_available):
    token, _ = login(client)
    resp = client.get("/api/analytics/monthly-trends", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert "monthly_trends" in data
    assert isinstance(data["monthly_trends"], list)


def test_admin_ping(client, db_available):
    token, _ = login(client)  # john_doe is admin in sample data
    resp = client.get("/api/admin/ping", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json().get("message") == "admin ok"
