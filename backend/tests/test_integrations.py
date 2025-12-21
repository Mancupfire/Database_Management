import json
import sys
from datetime import date
from pathlib import Path

import pytest

# Ensure backend package is on path when running pytest from backend/
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from database import Database


@pytest.fixture(scope="session", autouse=True)
def ensure_env():
    # Ensure we point to test DB if provided
    return


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
        pytest.skip("Database not reachable on configured host; skipping integration tests.")
    return True


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


def test_budget_status_endpoint(client, db_available):
    token, _ = login(client)
    resp = client.get("/api/analytics/budget-status", headers=auth_headers(token))
    assert resp.status_code == 200
    payload = resp.get_json()
    assert "budgets" in payload
    assert isinstance(payload["budgets"], list)
    if payload["budgets"]:
        sample = payload["budgets"][0]
        for key in ["budget_id", "category_id", "amount_limit", "spent", "status", "percentage"]:
            assert key in sample


def test_unusual_spending_view(client, db_available):
    token, _ = login(client)
    resp = client.get("/api/analytics/unusual-spending", headers=auth_headers(token))
    assert resp.status_code == 200
    payload = resp.get_json()
    assert "alerts" in payload
    assert isinstance(payload["alerts"], list)
    if payload["alerts"]:
        alert = payload["alerts"][0]
        for key in ["category_id", "average_spent", "max_spent", "alert_threshold"]:
            assert key in alert


def test_recurring_procedure_creates_transaction(db_available):
    """
    Create a temporary recurring payment, run SP_Create_Recurring_Transaction,
    and ensure a new transaction is inserted plus the due date advances.
    """
    recurring_id = None
    initial_due_date = date.today()

    with Database.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO Recurring_Payments (user_id, account_id, category_id, amount, frequency, start_date, next_due_date, is_active)
                VALUES (%s, %s, %s, %s, 'Monthly', %s, %s, TRUE)
                """,
                (1, 1, 1, 111111.11, initial_due_date, initial_due_date),
            )
            recurring_id = cursor.lastrowid
            conn.commit()

    try:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT next_due_date FROM Recurring_Payments WHERE recurring_id = %s",
                    (recurring_id,),
                )
                before_due = cursor.fetchone()["next_due_date"]
                cursor.execute(
                    "SELECT COUNT(*) AS cnt FROM Transactions WHERE recurring_id = %s",
                    (recurring_id,),
                )
                before_count = cursor.fetchone()["cnt"]

        Database.call_procedure("SP_Create_Recurring_Transaction", (recurring_id,))

        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) AS cnt FROM Transactions WHERE recurring_id = %s",
                    (recurring_id,),
                )
                after_count = cursor.fetchone()["cnt"]
                cursor.execute(
                    "SELECT next_due_date FROM Recurring_Payments WHERE recurring_id = %s",
                    (recurring_id,),
                )
                after_due = cursor.fetchone()["next_due_date"]

        assert after_count == before_count + 1
        assert after_due > before_due
    finally:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM Transactions WHERE recurring_id = %s", (recurring_id,))
                cursor.execute("DELETE FROM Recurring_Payments WHERE recurring_id = %s", (recurring_id,))
            conn.commit()
