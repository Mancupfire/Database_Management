# MoneyMinder Performance Tuning Notes

This documents the tuning actions and how to verify them (aligned with the rubric).

## Indexing Changes
- Transactions:
  - `idx_transactions_date`, `idx_transactions_user_date`, `idx_transactions_alert`
  - **New:** `idx_transactions_user_category_date` (budgets/analytics filters)
  - **New:** `idx_transactions_group_date` (group expenses)
- Recurring_Payments:
  - **New:** `idx_recurring_due_date` (scheduler/next-due queries)
- Users:
  - `idx_users_email` (login)

## Verification Queries (before/after)
Run with a realistic dataset loaded:
```bash
mysql -u root -p MoneyMinder_DB -e "
EXPLAIN ANALYZE
SELECT t.transaction_id
FROM Transactions t
JOIN Categories c ON t.category_id = c.category_id
WHERE t.user_id = 1
  AND t.category_id = 1
  AND t.transaction_date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY t.transaction_date DESC
LIMIT 20;"
```
Expected: uses `idx_transactions_user_category_date` for range + order by.

```bash
mysql -u root -p MoneyMinder_DB -e "
EXPLAIN ANALYZE
SELECT b.budget_id, SUM(t.amount)
FROM Budgets b
LEFT JOIN Transactions t
  ON t.category_id = b.category_id
  AND t.user_id = b.user_id
  AND t.transaction_date BETWEEN b.start_date AND b.end_date
WHERE b.user_id = 1
GROUP BY b.budget_id;"
```
Expected: uses `idx_transactions_user_category_date`.

```bash
mysql -u root -p MoneyMinder_DB -e "
EXPLAIN ANALYZE
SELECT recurring_id
FROM Recurring_Payments
WHERE user_id = 1 AND next_due_date <= CURDATE();"
```
Expected: uses `idx_recurring_due_date`.

## Suggested Partitioning (optional)
If Transactions grows large, consider RANGE partitioning by YEAR(transaction_date). Example DDL (run after backup):
```sql
ALTER TABLE Transactions
PARTITION BY RANGE (YEAR(transaction_date)) (
  PARTITION p2023 VALUES LESS THAN (2024),
  PARTITION p2024 VALUES LESS THAN (2025),
  PARTITION pmax  VALUES LESS THAN MAXVALUE
);
```
Measure `EXPLAIN ANALYZE` before/after on date-filtered queries.

## How to Capture Evidence
1) Collect `EXPLAIN ANALYZE` output (before/after index/partition changes).
   - Quick helper: `MYSQL_USER=root MYSQL_PASSWORD=... MYSQL_DB=MoneyMinder_DB ./scripts/run_explain.sh` → saves to `docs/perf_results.txt`.
2) Note timing improvements and index usage in your report/slides.
3) For workloads, you can simulate inserts with:
```bash
mysql -u root -p MoneyMinder_DB -e "
CALL SP_Create_Recurring_Transaction(1);
SELECT COUNT(*) FROM Transactions;"
```
4) Keep the captured plans/timings (or screenshot `docs/perf_results.txt`) in your presentation/report to satisfy the rubric. 
