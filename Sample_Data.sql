-- ==========================================================
-- SAMPLE DATA FOR MONEYMINDER DEMO
-- ==========================================================
-- This file contains realistic test data for demonstration purposes

USE MoneyMinder_DB;

-- ==========================================================
-- 1. TEST USERS
-- ==========================================================
-- Password for all users: "Demo@2024" (bcrypt hashed)

INSERT INTO Users (username, email, password_hash, base_currency, created_at) VALUES 
('john_doe', 'john.doe@example.com', '$2b$12$Uin1HqNfQFTLFSVrt6pEXeVJs22kEm78reC57/oeIrqn4XvE31wCu', 'VND', '2024-01-15 10:00:00'),
('jane_smith', 'jane.smith@example.com', '$2b$12$Uin1HqNfQFTLFSVrt6pEXeVJs22kEm78reC57/oeIrqn4XvE31wCu', 'USD', '2024-02-20 14:30:00'),
('nguyen_van_a', 'nguyenvana@example.com', '$2b$12$Uin1HqNfQFTLFSVrt6pEXeVJs22kEm78reC57/oeIrqn4XvE31wCu', 'VND', '2024-03-10 09:15:00'),
('tran_thi_b', 'tranthib@example.com', '$2b$12$Uin1HqNfQFTLFSVrt6pEXeVJs22kEm78reC57/oeIrqn4XvE31wCu', 'VND', '2024-03-12 11:20:00');

-- ==========================================================
-- 2. GROUPS (Shared Expenses)
-- ==========================================================

INSERT INTO `Groups` (group_name, created_by, created_at) VALUES 
('Family Budget', 1, '2024-01-20 10:00:00'),
('Roommates - Apartment 203', 3, '2024-03-15 14:00:00'),
('Vietnam Trip 2024', 2, '2024-06-01 08:00:00');

-- ==========================================================
-- 3. GROUP MEMBERSHIPS
-- ==========================================================

INSERT INTO User_Groups (user_id, group_id, joined_at) VALUES 
-- Family Budget group
(1, 1, '2024-01-20 10:00:00'),
(2, 1, '2024-01-20 10:05:00'),

-- Roommates group
(3, 2, '2024-03-15 14:00:00'),
(4, 2, '2024-03-15 14:10:00'),

-- Vietnam Trip group
(2, 3, '2024-06-01 08:00:00'),
(3, 3, '2024-06-01 08:15:00'),
(4, 3, '2024-06-01 08:20:00');

-- ==========================================================
-- 4. ACCOUNTS (Wallets, Banks, etc.)
-- ==========================================================

-- John's accounts
INSERT INTO Accounts (user_id, account_name, account_type, balance, created_at) VALUES 
(1, 'Cash Wallet', 'Cash', 2500000.00, '2024-01-15 10:30:00'),
(1, 'Vietcombank Savings', 'Bank Account', 50000000.00, '2024-01-15 10:35:00'),
(1, 'TPBank Credit Card', 'Credit Card', 0.00, '2024-01-15 10:40:00'),
(1, 'MoMo Wallet', 'E-Wallet', 1500000.00, '2024-01-15 10:45:00');

-- Jane's accounts
INSERT INTO Accounts (user_id, account_name, account_type, balance, created_at) VALUES 
(2, 'Cash USD', 'Cash', 500.00, '2024-02-20 15:00:00'),
(2, 'Chase Checking', 'Bank Account', 5000.00, '2024-02-20 15:05:00'),
(2, 'ZaloPay', 'E-Wallet', 800000.00, '2024-02-20 15:10:00');

-- Nguyen Van A's accounts
INSERT INTO Accounts (user_id, account_name, account_type, balance, created_at) VALUES 
(3, 'Cash', 'Cash', 1200000.00, '2024-03-10 09:30:00'),
(3, 'Techcombank', 'Bank Account', 15000000.00, '2024-03-10 09:35:00'),
(3, 'MoMo', 'E-Wallet', 500000.00, '2024-03-10 09:40:00');

-- Tran Thi B's accounts
INSERT INTO Accounts (user_id, account_name, account_type, balance, created_at) VALUES 
(4, 'Cash', 'Cash', 800000.00, '2024-03-12 11:30:00'),
(4, 'VPBank', 'Bank Account', 20000000.00, '2024-03-12 11:35:00');

-- ==========================================================
-- 5. USER CUSTOM CATEGORIES
-- ==========================================================

-- John's custom categories
INSERT INTO Categories (user_id, category_name, type) VALUES 
(1, 'Coffee & Snacks', 'Expense'),
(1, 'Gym Membership', 'Expense'),
(1, 'Side Project Income', 'Income');

-- Jane's custom categories
INSERT INTO Categories (user_id, category_name, type) VALUES 
(2, 'Photography Gear', 'Expense'),
(2, 'Consulting Income', 'Income');

-- ==========================================================
-- 6. BUDGETS
-- ==========================================================

-- John's budgets for March 2024
INSERT INTO Budgets (user_id, category_id, amount_limit, start_date, end_date) VALUES 
(1, 1, 3000000.00, '2024-03-01', '2024-03-31'),  -- Food & Beverage
(1, 2, 2000000.00, '2024-03-01', '2024-03-31'),  -- Transportation
(1, 5, 1000000.00, '2024-03-01', '2024-03-31');  -- Entertainment

-- Jane's budgets
INSERT INTO Budgets (user_id, category_id, amount_limit, start_date, end_date) VALUES 
(2, 1, 300.00, '2024-03-01', '2024-03-31'),      -- Food & Beverage (USD)
(2, 8, 500.00, '2024-03-01', '2024-03-31');      -- Shopping (USD)

-- ==========================================================
-- 7. RECURRING PAYMENTS
-- ==========================================================

INSERT INTO Recurring_Payments (user_id, account_id, category_id, amount, frequency, start_date, next_due_date, is_active) VALUES 
-- John's subscriptions
(1, 2, 3, 5000000.00, 'Monthly', '2024-01-01', '2024-04-01', TRUE),  -- Rent
(1, 4, 4, 500000.00, 'Monthly', '2024-01-01', '2024-04-01', TRUE),   -- Utilities
(1, 1, 13, 199000.00, 'Monthly', '2024-02-01', '2024-04-01', TRUE),  -- Gym (custom category)

-- Jane's subscriptions
(2, 3, 5, 15.00, 'Monthly', '2024-02-01', '2024-04-01', TRUE),       -- Entertainment (Netflix-like)
(2, 2, 3, 1200.00, 'Monthly', '2024-02-01', '2024-04-01', TRUE);     -- Rent (USD)

-- ==========================================================
-- 8. TRANSACTIONS (Historical Data)
-- ==========================================================

-- John's transactions (January - March 2024)
INSERT INTO Transactions (user_id, account_id, category_id, group_id, recurring_id, amount, original_amount, currency_code, exchange_rate, transaction_date, description) VALUES 
-- Income
(1, 2, 9, NULL, NULL, 25000000.00, NULL, 'VND', 1.0, '2024-01-05 09:00:00', 'Monthly Salary - January'),
(1, 2, 9, NULL, NULL, 25000000.00, NULL, 'VND', 1.0, '2024-02-05 09:00:00', 'Monthly Salary - February'),
(1, 2, 9, NULL, NULL, 25000000.00, NULL, 'VND', 1.0, '2024-03-05 09:00:00', 'Monthly Salary - March'),

-- Rent (Recurring)
(1, 2, 3, NULL, 1, 5000000.00, NULL, 'VND', 1.0, '2024-01-01 08:00:00', 'Recurring payment - Monthly'),
(1, 2, 3, NULL, 1, 5000000.00, NULL, 'VND', 1.0, '2024-02-01 08:00:00', 'Recurring payment - Monthly'),
(1, 2, 3, NULL, 1, 5000000.00, NULL, 'VND', 1.0, '2024-03-01 08:00:00', 'Recurring payment - Monthly'),

-- Utilities (Recurring - with unusual spike in March)
(1, 4, 4, NULL, 2, 450000.00, NULL, 'VND', 1.0, '2024-01-15 10:00:00', 'Recurring payment - Monthly'),
(1, 4, 4, NULL, 2, 480000.00, NULL, 'VND', 1.0, '2024-02-15 10:00:00', 'Recurring payment - Monthly'),
(1, 4, 4, NULL, 2, 850000.00, NULL, 'VND', 1.0, '2024-03-15 10:00:00', 'Recurring payment - Monthly - UNUSUAL SPIKE!'),

-- Food & Beverage
(1, 4, 1, NULL, NULL, 250000.00, NULL, 'VND', 1.0, '2024-03-01 12:30:00', 'Lunch at restaurant'),
(1, 1, 1, NULL, NULL, 45000.00, NULL, 'VND', 1.0, '2024-03-02 08:00:00', 'Breakfast - Pho'),
(1, 4, 1, NULL, NULL, 350000.00, NULL, 'VND', 1.0, '2024-03-05 19:00:00', 'Dinner with family'),
(1, 4, 1, NULL, NULL, 120000.00, NULL, 'VND', 1.0, '2024-03-08 13:00:00', 'Coffee meeting'),

-- Transportation
(1, 4, 2, NULL, NULL, 150000.00, NULL, 'VND', 1.0, '2024-03-03 07:30:00', 'Grab to office'),
(1, 1, 2, NULL, NULL, 30000.00, NULL, 'VND', 1.0, '2024-03-06 18:00:00', 'Bus ticket'),
(1, 4, 2, NULL, NULL, 500000.00, NULL, 'VND', 1.0, '2024-03-10 15:00:00', 'Gasoline'),

-- Entertainment
(1, 1, 5, NULL, NULL, 180000.00, NULL, 'VND', 1.0, '2024-03-12 20:00:00', 'Movie tickets'),
(1, 4, 5, NULL, NULL, 450000.00, NULL, 'VND', 1.0, '2024-03-14 21:00:00', 'Dinner & drinks with friends');

-- Jane's transactions (Multi-currency examples)
INSERT INTO Transactions (user_id, account_id, category_id, group_id, recurring_id, amount, original_amount, currency_code, exchange_rate, transaction_date, description) VALUES 
-- Income (USD)
(2, 2, 15, NULL, NULL, 3000.00, NULL, 'USD', 1.0, '2024-03-01 09:00:00', 'Consulting project payment'),

-- Expenses in USD
(2, 2, 1, NULL, NULL, 45.00, NULL, 'USD', 1.0, '2024-03-03 12:00:00', 'Lunch - Chipotle'),
(2, 2, 8, NULL, NULL, 89.99, NULL, 'USD', 1.0, '2024-03-05 14:30:00', 'New headphones'),

-- Multi-currency: Spending in Vietnam (user base is USD, spent in VND)
(2, 3, 1, NULL, NULL, 25.00, 575000.00, 'USD', 23000.00, '2024-03-15 13:00:00', 'Lunch in Hanoi'),
(2, 3, 2, NULL, NULL, 10.00, 230000.00, 'USD', 23000.00, '2024-03-15 15:00:00', 'Taxi in Hanoi');

-- Nguyen Van A's transactions
INSERT INTO Transactions (user_id, account_id, category_id, group_id, recurring_id, amount, original_amount, currency_code, exchange_rate, transaction_date, description) VALUES 
(3, 2, 9, NULL, NULL, 15000000.00, NULL, 'VND', 1.0, '2024-03-05 09:00:00', 'Salary - March'),
(3, 3, 1, NULL, NULL, 85000.00, NULL, 'VND', 1.0, '2024-03-07 12:00:00', 'Lunch'),
(3, 3, 2, NULL, NULL, 25000.00, NULL, 'VND', 1.0, '2024-03-08 08:00:00', 'Bus fare'),
(3, 1, 1, NULL, NULL, 150000.00, NULL, 'VND', 1.0, '2024-03-10 19:00:00', 'Dinner'),

-- Group expense for Roommates
(3, 2, 4, 2, NULL, 1500000.00, NULL, 'VND', 1.0, '2024-03-15 10:00:00', 'Shared electricity bill'),
(4, 2, 4, 2, NULL, 1500000.00, NULL, 'VND', 1.0, '2024-03-15 10:05:00', 'Shared electricity bill');

-- Tran Thi B's transactions
INSERT INTO Transactions (user_id, account_id, category_id, group_id, recurring_id, amount, original_amount, currency_code, exchange_rate, transaction_date, description) VALUES 
(4, 2, 9, NULL, NULL, 18000000.00, NULL, 'VND', 1.0, '2024-03-05 09:00:00', 'Salary - March'),
(4, 1, 1, NULL, NULL, 65000.00, NULL, 'VND', 1.0, '2024-03-06 12:30:00', 'Lunch'),
(4, 1, 8, NULL, NULL, 250000.00, NULL, 'VND', 1.0, '2024-03-09 15:00:00', 'Shopping - Clothes');

-- ==========================================================
-- VERIFICATION QUERIES (Optional - for testing)
-- ==========================================================

-- Check total users
-- SELECT COUNT(*) as total_users FROM Users;

-- Check all accounts with balances
-- SELECT u.username, a.account_name, a.account_type, a.balance 
-- FROM Accounts a JOIN Users u ON a.user_id = u.user_id;

-- Check recent transactions
-- SELECT u.username, t.amount, c.category_name, t.transaction_date, t.description
-- FROM Transactions t
-- JOIN Users u ON t.user_id = u.user_id
-- JOIN Categories c ON t.category_id = c.category_id
-- ORDER BY t.transaction_date DESC LIMIT 10;

-- Check monthly report
-- SELECT * FROM View_Monthly_Report WHERE user_id = 1 ORDER BY month_year DESC;

-- Check unusual spending alert stats
-- SELECT * FROM View_Category_Alert_Stats WHERE user_id = 1;
