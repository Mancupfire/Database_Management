#!/usr/bin/env bash
set -euo pipefail

# Capture EXPLAIN ANALYZE output for key queries into docs/perf_results.txt
# Usage:
#   MYSQL_USER=root MYSQL_PASSWORD=yourpass MYSQL_DB=MoneyMinder_DB ./scripts/run_explain.sh

USER_NAME="${MYSQL_USER:-root}"
USER_PASS="${MYSQL_PASSWORD:-}"
DB_NAME="${MYSQL_DB:-MoneyMinder_DB}"
HOST="${MYSQL_HOST:-localhost}"

OUTPUT_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/docs/perf_results.txt"

run_query() {
  local label="$1"
  local sql="$2"
  {
    echo "===== ${label} ====="
    echo "${sql}"
    mysql -u "${USER_NAME}" -p"${USER_PASS}" -h "${HOST}" "${DB_NAME}" -e "${sql}"
    echo
  } >> "${OUTPUT_FILE}"
}

echo "Writing EXPLAIN ANALYZE output to ${OUTPUT_FILE}"
date > "${OUTPUT_FILE}"
echo >> "${OUTPUT_FILE}"

run_query "Txn by user/category/date" "
EXPLAIN ANALYZE
SELECT t.transaction_id
FROM Transactions t
JOIN Categories c ON t.category_id = c.category_id
WHERE t.user_id = 1
  AND t.category_id = 1
  AND t.transaction_date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY t.transaction_date DESC
LIMIT 20;"

run_query "Budgets with date-range txn join" "
EXPLAIN ANALYZE
SELECT b.budget_id, SUM(t.amount)
FROM Budgets b
LEFT JOIN Transactions t
  ON t.category_id = b.category_id
  AND t.user_id = b.user_id
  AND t.transaction_date BETWEEN b.start_date AND b.end_date
WHERE b.user_id = 1
GROUP BY b.budget_id;"

run_query "Recurring payments due" "
EXPLAIN ANALYZE
SELECT recurring_id
FROM Recurring_Payments
WHERE user_id = 1 AND next_due_date <= CURDATE();"

echo "Done."
