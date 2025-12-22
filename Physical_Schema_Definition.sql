-- ==========================================================
-- 1. DATABASE INITIALIZATION
-- ==========================================================
DROP DATABASE IF EXISTS MoneyMinder_DB;
CREATE DATABASE MoneyMinder_DB;
USE MoneyMinder_DB;

-- ==========================================================
-- 2. TABLE DEFINITIONS
-- ==========================================================

-- 1. Users: Stores credentials and global settings
CREATE TABLE Users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    base_currency VARCHAR(3) DEFAULT 'VND', -- e.g., VND, USD
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Groups: For shared expenses (Family, Trip, Roommates)
CREATE TABLE `Groups` (
    group_id INT PRIMARY KEY AUTO_INCREMENT,
    group_name VARCHAR(100) NOT NULL,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES Users(user_id) ON DELETE SET NULL
);

-- 3. User_Groups: Many-to-Many link (Who is in which group)
CREATE TABLE User_Groups (
    user_id INT,
    group_id INT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES `Groups`(group_id) ON DELETE CASCADE
);

-- 4. Accounts: Wallets, Banks, etc.
CREATE TABLE Accounts (
    account_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    account_name VARCHAR(50) NOT NULL, 
    -- FIXED: Changed to ENUM for consistency and safety
    account_type ENUM('Cash', 'Bank Account', 'Credit Card', 'E-Wallet', 'Investment') NOT NULL, 
    balance DECIMAL(15, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 5. Categories: Spending types (System default or User custom)
CREATE TABLE Categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT DEFAULT NULL, -- NULL = System Default (Global), NOT NULL = Custom User Category
    category_name VARCHAR(50) NOT NULL, 
    type ENUM('Income', 'Expense') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 6. Budgets: Spending limits (REQUIRED by your proposal)
CREATE TABLE Budgets (
    budget_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    amount_limit DECIMAL(15, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON DELETE CASCADE
);

-- 7. Recurring_Payments: Subscription definitions
CREATE TABLE Recurring_Payments (
    recurring_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    account_id INT NOT NULL,   
    category_id INT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    frequency ENUM('Daily', 'Weekly', 'Monthly', 'Yearly') NOT NULL,
    start_date DATE NOT NULL,
    next_due_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES Accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id)
);

-- 8. Transactions: The central financial history
CREATE TABLE Transactions (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    account_id INT NOT NULL,
    category_id INT NOT NULL,
    group_id INT DEFAULT NULL, -- Nullable (only for shared expenses)
    recurring_id INT DEFAULT NULL, -- FIXED: Link to Recurring_Payments
    
    -- Financials
    amount DECIMAL(15, 2) NOT NULL, 
    original_amount DECIMAL(15, 2),            -- For Multi-Currency support
    currency_code VARCHAR(3) DEFAULT 'VND',    
    exchange_rate DECIMAL(15, 6) DEFAULT 1.0,  
    
    transaction_date DATETIME NOT NULL,
    description TEXT,
    
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES Accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id),
    FOREIGN KEY (group_id) REFERENCES `Groups`(group_id) ON DELETE SET NULL,
    FOREIGN KEY (recurring_id) REFERENCES Recurring_Payments(recurring_id) ON DELETE SET NULL
);

-- ==========================================================
-- 3. INDEX DEFINITIONS (Performance Optimization)
-- ==========================================================

-- Speed up login
CREATE INDEX idx_users_email ON Users(email);

-- Speed up filtering transactions by date
CREATE INDEX idx_transactions_date ON Transactions(transaction_date);

-- Speed up "Show my history" queries
CREATE INDEX idx_transactions_user_date ON Transactions(user_id, transaction_date);

-- Speed up "Alert" calculation (Finding average for a specific category)
CREATE INDEX idx_transactions_alert ON Transactions(user_id, category_id, amount);

-- ==========================================================
-- 4. VIEW DEFINITIONS (Logic Layer)
-- ==========================================================

-- VIEW 1: Unusual Spending Alert Logic
-- Calculates the average spending per category for the last 6 months.
-- Your Backend can query this to decide if a new bill is "Unusual".
CREATE OR REPLACE VIEW View_Category_Alert_Stats AS
SELECT 
    user_id,
    category_id,
    AVG(amount) as average_spent,
    MAX(amount) as max_spent
FROM Transactions
WHERE transaction_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
GROUP BY user_id, category_id;

-- VIEW 2: Monthly Report
-- Simple aggregation for charts and graphs.
CREATE OR REPLACE VIEW View_Monthly_Report AS
SELECT 
    t.user_id,
    DATE_FORMAT(t.transaction_date, '%Y-%m') AS month_year,
    c.category_name,
    c.type,
    SUM(t.amount) AS total_amount
FROM Transactions t
JOIN Categories c ON t.category_id = c.category_id
GROUP BY t.user_id, month_year, c.category_name, c.type;

-- VIEW 3: Unusual Spending Alert View
-- Pre-calculates the rolling average and maximum spending per category for each user over the last 6 months.
-- Use Case: Backend queries this view before inserting a new transaction. If the new transaction amount
-- exceeds average_spent × 1.25, the system triggers an "Unusual Spending" alert.
CREATE OR REPLACE VIEW View_Unusual_Spending_Alert AS
SELECT 
    t.user_id,
    t.category_id,
    c.category_name,
    COUNT(t.transaction_id) as transaction_count,
    AVG(t.amount) as average_spent,
    MAX(t.amount) as max_spent,
    STDDEV(t.amount) as std_deviation,
    AVG(t.amount) * 1.25 as alert_threshold
FROM Transactions t
JOIN Categories c ON t.category_id = c.category_id
WHERE t.transaction_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
  AND c.type = 'Expense'
GROUP BY t.user_id, t.category_id, c.category_name
HAVING COUNT(t.transaction_id) >= 3;  -- Need at least 3 transactions to establish pattern

-- VIEW 4: Group Expense Summary View
-- Calculates the total contribution of each member within shared groups.
-- Use Case: Displayed on the "Group Details" page to show who has spent the most 
-- and to help settle debts between roommates or travel companions.
CREATE OR REPLACE VIEW View_Group_Expense_Summary AS
SELECT 
    t.group_id,
    g.group_name,
    t.user_id,
    u.username,
    u.email,
    COUNT(DISTINCT t.transaction_id) as transaction_count,
    SUM(CASE WHEN c.type = 'Expense' THEN ABS(t.amount) ELSE 0 END) as total_expenses,
    SUM(CASE WHEN c.type = 'Income' THEN t.amount ELSE 0 END) as total_contributions,
    SUM(CASE WHEN c.type = 'Expense' THEN ABS(t.amount) ELSE -t.amount END) as net_spending,
    ROUND(SUM(CASE WHEN c.type = 'Expense' THEN ABS(t.amount) ELSE 0 END) / 
          NULLIF((SELECT COUNT(DISTINCT ug.user_id) 
                  FROM User_Groups ug 
                  WHERE ug.group_id = t.group_id), 0), 2) as fair_share,
    ROUND(SUM(CASE WHEN c.type = 'Expense' THEN ABS(t.amount) ELSE 0 END) - 
          (SUM(CASE WHEN c.type = 'Expense' THEN ABS(t.amount) ELSE 0 END) / 
           NULLIF((SELECT COUNT(DISTINCT ug.user_id) 
                   FROM User_Groups ug 
                   WHERE ug.group_id = t.group_id), 0)), 2) as balance_owed
FROM Transactions t
JOIN `Groups` g ON t.group_id = g.group_id
JOIN Users u ON t.user_id = u.user_id
JOIN Categories c ON t.category_id = c.category_id
WHERE t.group_id IS NOT NULL
GROUP BY t.group_id, g.group_name, t.user_id, u.username, u.email;

-- VIEW 5: Upcoming Recurring Payments View
-- Identifies active subscriptions that are due for payment within the next 7 days.
-- Use Case: Displayed as a "Upcoming Bills" notification widget on the user's home screen.
CREATE OR REPLACE VIEW View_Upcoming_Recurring_Payments AS
SELECT 
    rp.recurring_id,
    rp.user_id,
    u.username,
    u.email,
    rp.account_id,
    a.account_name,
    rp.category_id,
    c.category_name,
    rp.amount,
    rp.frequency,
    rp.next_due_date,
    DATEDIFF(rp.next_due_date, CURDATE()) as days_until_due,
    CASE 
        WHEN DATEDIFF(rp.next_due_date, CURDATE()) = 0 THEN 'Due Today'
        WHEN DATEDIFF(rp.next_due_date, CURDATE()) = 1 THEN 'Due Tomorrow'
        WHEN DATEDIFF(rp.next_due_date, CURDATE()) < 0 THEN 'Overdue'
        ELSE CONCAT('Due in ', DATEDIFF(rp.next_due_date, CURDATE()), ' days')
    END as due_status,
    CASE 
        WHEN DATEDIFF(rp.next_due_date, CURDATE()) < 0 THEN 'critical'
        WHEN DATEDIFF(rp.next_due_date, CURDATE()) <= 2 THEN 'high'
        WHEN DATEDIFF(rp.next_due_date, CURDATE()) <= 5 THEN 'medium'
        ELSE 'low'
    END as urgency_level
FROM Recurring_Payments rp
JOIN Users u ON rp.user_id = u.user_id
JOIN Accounts a ON rp.account_id = a.account_id
JOIN Categories c ON rp.category_id = c.category_id
WHERE rp.is_active = TRUE
  AND rp.next_due_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
ORDER BY rp.next_due_date ASC, rp.amount DESC;

-- ==========================================================
-- 5. STORED PROCEDURES (Business Logic)
-- ==========================================================

-- PROCEDURE 1: Create Recurring Transaction
-- Automatically generates a transaction from recurring payment and updates next due date
DELIMITER //
CREATE PROCEDURE SP_Create_Recurring_Transaction(
    IN p_recurring_id INT,
    IN p_transaction_datetime DATETIME
)
BEGIN
    DECLARE v_user_id INT;
    DECLARE v_account_id INT;
    DECLARE v_category_id INT;
    DECLARE v_amount DECIMAL(15, 2);
    DECLARE v_frequency VARCHAR(20);
    DECLARE v_next_due DATE;
    DECLARE v_transaction_date DATETIME;
    
    -- Use provided datetime from browser (local time as-is)
    IF p_transaction_datetime IS NOT NULL THEN
        SET v_transaction_date = p_transaction_datetime;
    ELSE
        SET v_transaction_date = NOW();
    END IF;
    
    -- Get recurring payment details
    SELECT user_id, account_id, category_id, amount, frequency, next_due_date
    INTO v_user_id, v_account_id, v_category_id, v_amount, v_frequency, v_next_due
    FROM Recurring_Payments
    WHERE recurring_id = p_recurring_id AND is_active = TRUE;
    
    -- Insert transaction with specified datetime
    INSERT INTO Transactions (user_id, account_id, category_id, recurring_id, amount, transaction_date, description)
    VALUES (v_user_id, v_account_id, v_category_id, p_recurring_id, v_amount, v_transaction_date, 
            CONCAT('Recurring payment - ', v_frequency));

    
    -- Update next due date based on frequency
    UPDATE Recurring_Payments
    SET next_due_date = CASE 
        WHEN frequency = 'Daily' THEN DATE_ADD(next_due_date, INTERVAL 1 DAY)
        WHEN frequency = 'Weekly' THEN DATE_ADD(next_due_date, INTERVAL 1 WEEK)
        WHEN frequency = 'Monthly' THEN DATE_ADD(next_due_date, INTERVAL 1 MONTH)
        WHEN frequency = 'Yearly' THEN DATE_ADD(next_due_date, INTERVAL 1 YEAR)
    END
    WHERE recurring_id = p_recurring_id;
END //
DELIMITER ;

-- PROCEDURE 2: Check Budget Alert
-- Checks if user has exceeded budget limit for a specific category
DELIMITER //
CREATE PROCEDURE SP_Check_Budget_Alert(
    IN p_user_id INT,
    IN p_category_id INT,
    IN p_start_date DATE,
    IN p_end_date DATE,
    OUT p_budget_limit DECIMAL(15, 2),
    OUT p_total_spent DECIMAL(15, 2),
    OUT p_percentage_used DECIMAL(5, 2),
    OUT p_alert_status VARCHAR(20)
)
BEGIN
    -- Get budget limit
    SELECT amount_limit INTO p_budget_limit
    FROM Budgets
    WHERE user_id = p_user_id 
    AND category_id = p_category_id
    AND start_date <= p_start_date 
    AND end_date >= p_end_date
    LIMIT 1;
    
    -- Calculate total spent
    SELECT COALESCE(SUM(amount), 0) INTO p_total_spent
    FROM Transactions
    WHERE user_id = p_user_id 
    AND category_id = p_category_id
    AND transaction_date BETWEEN p_start_date AND p_end_date;
    
    -- Calculate percentage
    IF p_budget_limit IS NOT NULL AND p_budget_limit > 0 THEN
        SET p_percentage_used = (p_total_spent / p_budget_limit) * 100;
        
        -- Set alert status
        SET p_alert_status = CASE
            WHEN p_percentage_used >= 100 THEN 'EXCEEDED'
            WHEN p_percentage_used >= 80 THEN 'WARNING'
            WHEN p_percentage_used >= 50 THEN 'NORMAL'
            ELSE 'SAFE'
        END;
    ELSE
        SET p_percentage_used = 0;
        SET p_alert_status = 'NO_BUDGET';
    END IF;
END //
DELIMITER ;

-- ==========================================================
-- 6. TRIGGERS (Automated Actions)
-- ==========================================================

-- TRIGGER 1: Update Account Balance on Transaction Insert
DELIMITER //
CREATE TRIGGER TRG_Update_Account_Balance_Insert
AFTER INSERT ON Transactions
FOR EACH ROW
BEGIN
    DECLARE v_category_type VARCHAR(10);
    
    -- Get category type (Income or Expense)
    SELECT type INTO v_category_type
    FROM Categories
    WHERE category_id = NEW.category_id;
    
    -- Update account balance
    IF v_category_type = 'Income' THEN
        UPDATE Accounts
        SET balance = balance + NEW.amount
        WHERE account_id = NEW.account_id;
    ELSE
        UPDATE Accounts
        SET balance = balance - NEW.amount
        WHERE account_id = NEW.account_id;
    END IF;
END //
DELIMITER ;

-- TRIGGER 2: Update Account Balance on Transaction Delete
DELIMITER //
CREATE TRIGGER TRG_Update_Account_Balance_Delete
AFTER DELETE ON Transactions
FOR EACH ROW
BEGIN
    DECLARE v_category_type VARCHAR(10);
    
    -- Get category type (Income or Expense)
    SELECT type INTO v_category_type
    FROM Categories
    WHERE category_id = OLD.category_id;
    
    -- Reverse the balance change
    IF v_category_type = 'Income' THEN
        UPDATE Accounts
        SET balance = balance - OLD.amount
        WHERE account_id = OLD.account_id;
    ELSE
        UPDATE Accounts
        SET balance = balance + OLD.amount
        WHERE account_id = OLD.account_id;
    END IF;
END //
DELIMITER ;

-- TRIGGER 3: Update Account Balance on Transaction Update
DELIMITER //
CREATE TRIGGER TRG_Update_Account_Balance_Update
AFTER UPDATE ON Transactions
FOR EACH ROW
BEGIN
    DECLARE v_old_type VARCHAR(10);
    DECLARE v_new_type VARCHAR(10);
    
    -- Get old and new category types
    SELECT type INTO v_old_type FROM Categories WHERE category_id = OLD.category_id;
    SELECT type INTO v_new_type FROM Categories WHERE category_id = NEW.category_id;
    
    -- Reverse old transaction effect
    IF v_old_type = 'Income' THEN
        UPDATE Accounts SET balance = balance - OLD.amount WHERE account_id = OLD.account_id;
    ELSE
        UPDATE Accounts SET balance = balance + OLD.amount WHERE account_id = OLD.account_id;
    END IF;
    
    -- Apply new transaction effect
    IF v_new_type = 'Income' THEN
        UPDATE Accounts SET balance = balance + NEW.amount WHERE account_id = NEW.account_id;
    ELSE
        UPDATE Accounts SET balance = balance - NEW.amount WHERE account_id = NEW.account_id;
    END IF;
END //
DELIMITER ;

-- ==========================================================
-- 6. NOTIFICATIONS TABLE
-- ==========================================================

-- Notifications: Stores system notifications for users
CREATE TABLE Notifications (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    type ENUM('upcoming_bill', 'unusual_spending', 'budget_alert') NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity ENUM('info', 'warning', 'danger') DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    related_id INT NULL, -- Can reference transaction_id, recurring_id, or budget_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    INDEX idx_user_unread (user_id, is_read),
    INDEX idx_created_at (created_at)
);

-- ==========================================================
-- 7. SEED DATA (System Defaults & Test Data)
-- ==========================================================

-- Insert Default Categories (System-wide, user_id = NULL)
INSERT INTO Categories (user_id, category_name, type) VALUES 
(NULL, 'Food & Beverage', 'Expense'),
(NULL, 'Transportation', 'Expense'),
(NULL, 'Rent', 'Expense'),
(NULL, 'Utilities', 'Expense'),
(NULL, 'Entertainment', 'Expense'),
(NULL, 'Healthcare', 'Expense'),
(NULL, 'Education', 'Expense'),
(NULL, 'Shopping', 'Expense'),
(NULL, 'Salary', 'Income'),
(NULL, 'Freelance', 'Income'),
(NULL, 'Investment', 'Income'),
(NULL, 'Other', 'Income');

-- ==========================================================
-- 8. SECURITY CONFIGURATION
-- ==========================================================

-- Create MySQL Users with Different Privilege Levels
-- Note: Update passwords before production deployment

-- Admin User (Full Access)
CREATE USER IF NOT EXISTS 'moneyminder_admin'@'localhost' IDENTIFIED BY 'Admin@2024Secure!';
GRANT ALL PRIVILEGES ON MoneyMinder_DB.* TO 'moneyminder_admin'@'localhost';

-- Application User (CRUD Operations)
CREATE USER IF NOT EXISTS 'moneyminder_app'@'localhost' IDENTIFIED BY 'App@2024Secure!';
GRANT SELECT, INSERT, UPDATE, DELETE ON MoneyMinder_DB.* TO 'moneyminder_app'@'localhost';
GRANT EXECUTE ON MoneyMinder_DB.* TO 'moneyminder_app'@'localhost';

-- Read-Only User (Analytics/Reporting)
CREATE USER IF NOT EXISTS 'moneyminder_readonly'@'localhost' IDENTIFIED BY 'ReadOnly@2024Secure!';
GRANT SELECT ON MoneyMinder_DB.* TO 'moneyminder_readonly'@'localhost';

-- Apply privileges
FLUSH PRIVILEGES;