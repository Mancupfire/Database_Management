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
    password_hash_enc VARBINARY(512) NULL, -- encrypted copy of the hash (AES)
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
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

-- Speed up category/date filters (budgets, analytics, trends)
CREATE INDEX idx_transactions_user_category_date ON Transactions(user_id, category_id, transaction_date);

-- Speed up group expense lookups
CREATE INDEX idx_transactions_group_date ON Transactions(group_id, transaction_date);

-- Speed up recurring task scheduler (next due items per user)
CREATE INDEX idx_recurring_due_date ON Recurring_Payments(user_id, next_due_date);

-- Encryption key helper (change the seed before production)
DROP FUNCTION IF EXISTS FN_Get_Encryption_Key;
DELIMITER //
CREATE FUNCTION FN_Get_Encryption_Key()
RETURNS BINARY(32)
DETERMINISTIC
RETURN UNHEX(SHA2('MoneyMinder-Encryption-Key-ChangeMe', 256));
//
DELIMITER ;

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

-- VIEW 3: Monthly Trends with Window Functions
-- Provides running totals and rolling 3-month averages using window functions
CREATE OR REPLACE VIEW View_Monthly_Trends_Window AS
SELECT
    user_id,
    month_year,
    type,
    monthly_total,
    SUM(monthly_total) OVER (
        PARTITION BY user_id, type
        ORDER BY month_year
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total,
    AVG(monthly_total) OVER (
        PARTITION BY user_id, type
        ORDER BY month_year
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rolling_avg_3m
FROM (
    SELECT
        t.user_id,
        DATE_FORMAT(t.transaction_date, '%Y-%m') AS month_year,
        c.type,
        SUM(t.amount) AS monthly_total
    FROM Transactions t
    JOIN Categories c ON t.category_id = c.category_id
    GROUP BY t.user_id, month_year, c.type
) monthly_totals;

-- VIEW 4: Users (with decrypted hash copy for audit/ops)
CREATE OR REPLACE VIEW View_Users_Secure AS
SELECT 
    user_id,
    username,
    email,
    CAST(AES_DECRYPT(password_hash_enc, FN_Get_Encryption_Key()) AS CHAR(255)) AS password_hash_decrypted,
    base_currency,
    created_at
FROM Users;

-- ==========================================================
-- 5. STORED PROCEDURES (Business Logic)
-- ==========================================================

-- PROCEDURE 1: Create Recurring Transaction
-- Automatically generates a transaction from recurring payment and updates next due date
DELIMITER //
CREATE PROCEDURE SP_Create_Recurring_Transaction(
    IN p_recurring_id INT
)
BEGIN
    DECLARE v_user_id INT;
    DECLARE v_account_id INT;
    DECLARE v_category_id INT;
    DECLARE v_amount DECIMAL(15, 2);
    DECLARE v_frequency VARCHAR(20);
    DECLARE v_next_due DATE;
    
    -- Get recurring payment details
    SELECT user_id, account_id, category_id, amount, frequency, next_due_date
    INTO v_user_id, v_account_id, v_category_id, v_amount, v_frequency, v_next_due
    FROM Recurring_Payments
    WHERE recurring_id = p_recurring_id AND is_active = TRUE;
    
    -- Insert transaction
    INSERT INTO Transactions (user_id, account_id, category_id, recurring_id, amount, transaction_date, description)
    VALUES (v_user_id, v_account_id, v_category_id, p_recurring_id, v_amount, v_next_due, 
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
CREATE USER IF NOT EXISTS 'moneyminder_admin'@'localhost' IDENTIFIED BY 'MM_Admin@2024!r3set';
GRANT ALL PRIVILEGES ON MoneyMinder_DB.* TO 'moneyminder_admin'@'localhost';

-- Application User (CRUD Operations)
CREATE USER IF NOT EXISTS 'moneyminder_app'@'localhost' IDENTIFIED BY 'MM_App@2024!r3set';
GRANT SELECT, INSERT, UPDATE, DELETE ON MoneyMinder_DB.* TO 'moneyminder_app'@'localhost';
GRANT EXECUTE ON MoneyMinder_DB.* TO 'moneyminder_app'@'localhost';

-- Read-Only User (Analytics/Reporting)
CREATE USER IF NOT EXISTS 'moneyminder_readonly'@'localhost' IDENTIFIED BY 'MM_Read@2024!r3set';
GRANT SELECT ON MoneyMinder_DB.* TO 'moneyminder_readonly'@'localhost';

-- Apply privileges
FLUSH PRIVILEGES;

-- Encrypt password hashes at rest (keeps bcrypt hash encrypted in DB)
DELIMITER //
CREATE TRIGGER TRG_Users_Encrypt_Insert
BEFORE INSERT ON Users
FOR EACH ROW
BEGIN
    SET NEW.password_hash_enc = AES_ENCRYPT(NEW.password_hash, FN_Get_Encryption_Key());
END//
DELIMITER ;

DELIMITER //
CREATE TRIGGER TRG_Users_Encrypt_Update
BEFORE UPDATE ON Users
FOR EACH ROW
BEGIN
    IF NEW.password_hash <> OLD.password_hash THEN
        SET NEW.password_hash_enc = AES_ENCRYPT(NEW.password_hash, FN_Get_Encryption_Key());
    END IF;
END//
DELIMITER ;
