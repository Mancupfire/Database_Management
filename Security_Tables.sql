-- ==========================================================
-- SECURITY TABLES FOR MONEYMINDER
-- Run this after Physical_Schema_Definition.sql
-- ==========================================================

USE MoneyMinder_DB;

-- ==========================================================
-- 1. LOGIN ATTEMPTS TABLE
-- Tracks failed login attempts for account lockout
-- ==========================================================

CREATE TABLE IF NOT EXISTS Login_Attempts (
    attempt_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,  -- IPv6 compatible
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT FALSE,
    user_agent VARCHAR(500) NULL,
    
    -- Indexes for efficient querying
    INDEX idx_email_time (email, attempted_at),
    INDEX idx_ip_time (ip_address, attempted_at),
    INDEX idx_attempted_at (attempted_at)
);

-- ==========================================================
-- 2. SECURITY AUDIT LOG TABLE
-- Stores security-relevant events for monitoring
-- ==========================================================

CREATE TABLE IF NOT EXISTS Security_Audit_Log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    event_type ENUM(
        'LOGIN_SUCCESS', 
        'LOGIN_FAILURE', 
        'ACCOUNT_LOCKED', 
        'ACCOUNT_UNLOCKED', 
        'RATE_LIMIT_EXCEEDED', 
        'REGISTRATION', 
        'PASSWORD_CHANGE',
        'INVALID_TOKEN'
    ) NOT NULL,
    user_id INT NULL,
    email VARCHAR(100) NULL,
    ip_address VARCHAR(45) NOT NULL,
    endpoint VARCHAR(255) NULL,
    details JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to Users (nullable for failed attempts)
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
    
    -- Indexes for efficient querying
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at),
    INDEX idx_ip (ip_address),
    INDEX idx_user_id (user_id),
    INDEX idx_email (email)
);

-- ==========================================================
-- 3. STORED PROCEDURE: Clean up old login attempts
-- Should be run periodically (e.g., daily via cron)
-- ==========================================================

DELIMITER //

CREATE PROCEDURE IF NOT EXISTS SP_Cleanup_Login_Attempts(
    IN p_retention_hours INT
)
BEGIN
    -- Default to 24 hours if not specified
    IF p_retention_hours IS NULL OR p_retention_hours <= 0 THEN
        SET p_retention_hours = 24;
    END IF;
    
    -- Delete old login attempts
    DELETE FROM Login_Attempts 
    WHERE attempted_at < DATE_SUB(NOW(), INTERVAL p_retention_hours HOUR);
    
    -- Return number of deleted rows
    SELECT ROW_COUNT() as deleted_count;
END //

DELIMITER ;

-- ==========================================================
-- 4. STORED PROCEDURE: Clean up old audit logs
-- Should be run periodically (e.g., weekly via cron)
-- ==========================================================

DELIMITER //

CREATE PROCEDURE IF NOT EXISTS SP_Cleanup_Audit_Logs(
    IN p_retention_days INT
)
BEGIN
    -- Default to 90 days if not specified
    IF p_retention_days IS NULL OR p_retention_days <= 0 THEN
        SET p_retention_days = 90;
    END IF;
    
    -- Delete old audit logs
    DELETE FROM Security_Audit_Log 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL p_retention_days DAY);
    
    -- Return number of deleted rows
    SELECT ROW_COUNT() as deleted_count;
END //

DELIMITER ;

-- ==========================================================
-- 5. VIEW: Recent Failed Login Attempts
-- Shows accounts with multiple failed attempts
-- ==========================================================

CREATE OR REPLACE VIEW View_Failed_Login_Summary AS
SELECT 
    email,
    COUNT(*) as failed_attempts,
    MAX(attempted_at) as last_attempt,
    GROUP_CONCAT(DISTINCT ip_address) as ip_addresses
FROM Login_Attempts
WHERE success = FALSE
  AND attempted_at >= DATE_SUB(NOW(), INTERVAL 15 MINUTE)
GROUP BY email
HAVING COUNT(*) >= 3
ORDER BY failed_attempts DESC;

-- ==========================================================
-- 6. VIEW: Security Events Summary
-- Shows recent security events for monitoring
-- ==========================================================

CREATE OR REPLACE VIEW View_Security_Events_Summary AS
SELECT 
    DATE(created_at) as event_date,
    event_type,
    COUNT(*) as event_count
FROM Security_Audit_Log
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(created_at), event_type
ORDER BY event_date DESC, event_count DESC;

-- ==========================================================
-- Grant permissions to application user
-- ==========================================================

GRANT SELECT, INSERT, DELETE ON MoneyMinder_DB.Login_Attempts TO 'moneyminder_app'@'localhost';
GRANT SELECT, INSERT ON MoneyMinder_DB.Security_Audit_Log TO 'moneyminder_app'@'localhost';
GRANT EXECUTE ON PROCEDURE MoneyMinder_DB.SP_Cleanup_Login_Attempts TO 'moneyminder_app'@'localhost';
GRANT EXECUTE ON PROCEDURE MoneyMinder_DB.SP_Cleanup_Audit_Logs TO 'moneyminder_app'@'localhost';

FLUSH PRIVILEGES;
