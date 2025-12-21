#!/usr/bin/env bash
set -euo pipefail

# Lightweight OLTP/load simulation: inserts N synthetic transactions for user 1.
# Usage: MYSQL_USER=root MYSQL_PASSWORD=... MYSQL_DB=MoneyMinder_DB N=100 ./scripts/load_sim.sh

USER_NAME="${MYSQL_USER:-root}"
USER_PASS="${MYSQL_PASSWORD:-}"
DB_NAME="${MYSQL_DB:-MoneyMinder_DB}"
HOST="${MYSQL_HOST:-localhost}"
COUNT="${N:-100}"

echo "Inserting ${COUNT} synthetic transactions into ${DB_NAME}..."

mysql -u "${USER_NAME}" -p"${USER_PASS}" -h "${HOST}" "${DB_NAME}" -e "
INSERT INTO Transactions (user_id, account_id, category_id, amount, transaction_date, description)
SELECT 1, 1, 1, RAND()*100000, NOW(), CONCAT('Load test txn ', t.n)
FROM (
  SELECT @row := @row + 1 AS n
  FROM (SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) a,
       (SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) b,
       (SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) c,
       (SELECT @row:=0) r
) t
WHERE t.n <= ${COUNT};
"

echo "Done. You can measure performance with EXPLAIN ANALYZE or query counts:"
echo "  mysql -u ${USER_NAME} -p****** -h ${HOST} ${DB_NAME} -e \"SELECT COUNT(*) FROM Transactions;\""
