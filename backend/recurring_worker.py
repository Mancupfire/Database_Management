"""
Lightweight recurring payment worker.

Polls Recurring_Payments for due items and calls SP_Create_Recurring_Transaction.
Intended to be run alongside the API (cron/systemd/forever). Defaults to a 60s loop.
"""
import os
import signal
import time
from datetime import datetime

from database import Database

POLL_SECONDS = int(os.getenv("RECURRING_POLL_SECONDS", "60"))


def process_due_recurring():
    """Find due recurring payments and trigger the stored procedure."""
    due_items = Database.execute_query(
        """
        SELECT recurring_id
        FROM Recurring_Payments
        WHERE is_active = TRUE
          AND next_due_date <= CURDATE()
        """,
        fetch_all=True,
    ) or []

    for item in due_items:
        rid = item["recurring_id"]
        Database.call_procedure("SP_Create_Recurring_Transaction", (rid,))
        print(f"[{datetime.now()}] Processed recurring_id={rid}")


def main():
    print(f"Starting recurring worker (interval={POLL_SECONDS}s)")

    stop_requested = False

    def handle_stop(signum, frame):
        nonlocal stop_requested
        stop_requested = True
        print("Stopping recurring worker...")

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    while not stop_requested:
        try:
            process_due_recurring()
        except Exception as exc:
            print(f"[{datetime.now()}] Worker error: {exc}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
