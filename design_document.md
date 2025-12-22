

Page
13
of 13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
Design document: Inventory management
system
1 Conceptual & Logical Design
1.1 Functional Requirements
These specify what the system must do, focusing on the capabilities required for the personal and group financial
management system.
1.1.1 User Management
• Create/Update/Delete Users: The system manages user accounts stored in the Users table, which includes
fields such as username, email, password hash, and a preferred base currency.
• Authentication: Users log in using credentials. The system must secure user sessions and ensure data privacy.
• Profile Settings: Users can update their default currency (e.g., VND, USD) which affects how reports are
calculated.
Example: A user registers with email ”student@vinuni.edu.vn” and sets base currency = ’VND’.
1.1.2 Group Management
• Manage Shared Groups: Users can create groups (stored in the Groups table) to track shared expenses (e.g.,
Family, Trip, Roommates).
• Associate Members: The User Groups table links users to groups, recording when they joined via joined at.
Example: User A creates a group named ”Da Nang Trip” and invites User B. Both can now view and add transactions
to this group.
1.1.3 Account & Category Management
• Manage Accounts: Financial sources are stored in the Accounts table with fields like account name, account type
(Cash, Bank, Credit), and current balance.
• Manage Categories: Categories are stored in the Categories table. The system supports both Global
Categories (where user id is NULL) and Custom Categories (linked to a specific user id).
Example: A user creates a ”Techcombank” account and a custom category named ”Cat Food”.
1.1.4 Transaction Management
• Create/Track Transactions: Income and expenses are recorded in the Transactions table, linking user id,
account id, and category id.
• Multi-Currency Support: Transactions support foreign currencies. The system stores original amount,
currency code, and the exchange rate applied at the moment of transaction.
Example: A user spends 10 USD for lunch. The system records original amount = 10, currency code = ’USD’, and
converts it to amount = 250,000 (VND) based on exchange rate = 25,000.
1.1.5 Recurring Payments
• Manage Subscriptions: Recurring bills are stored in the Recurring Payments table with fields for frequency
(Daily, Monthly, Yearly), start date, and next due date.
• Automated Tracking: The system uses these records to generate transaction history or notify users.
Example: A ”Netflix Subscription” of 260,000 VND is set to repeat Monthly. The system tracks the next due date
automatically.
COMP3030 - Fall 2025 1/13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
1.1.6 Budgeting & Alerts
• Manage Budgets: Users set spending limits in the Budgets table, defined by category id, amount limit,
and a time range (start date, end date).
• Unusual Spending Detection: The system compares new transactions against historical averages (calculated
via Views) to flag anomalies.
Example: A user sets a budget of 5,000,000 VND for ”Food”. If a single dinner costs 2,000,000 VND (exceeding
historical average), the system flags it.
1.2 Non-Functional Requirements
These define system qualities like performance, security, and maintainability.
• Performance: Reporting queries (e.g., ”Show my spending last month”) should return results in under 2 sec-
onds.
Example: A monthly report query uses an index on Transactions(user id, transaction date) for fast re-
trieval without scanning the whole table.
• Data Integrity: The database must strictly enforce financial accuracy. Money cannot be created or destroyed
without a record.
Example: Foreign Key constraints ensure a Transaction cannot exist without a valid Account. DECIMAL(15,2)
is used instead of FLOAT to prevent rounding errors.
• Security: Passwords must be hashed (e.g., bcrypt). Data access must be isolated; users cannot see transactions
of groups they do not belong to.
Example: SQL Injection prevention is handled by the backend, and the database stores password hash instead
of plain text.
• Reliability: The system must ensure Atomicity and Consistency (ACID properties).
Example: When a transaction is deleted, the related Account balance update must happen within the same
database transaction scope.
• Scalability: The schema supports future expansion, such as integrating real-time Exchange Rate APIs, without
altering the core structure.
Example: The Transactions table is designed to hold snapshot exchange rates, allowing the system to scale to
millions of historical records without recalculation overhead.
• Maintainability: The schema is fully normalized (up to 3NF) to reduce redundancy.
Example: Changing a User’s email address is done in one place (Users table) and automatically reflects across
all their Groups and Transactions.
COMP3030 - Fall 2025 2/13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
1.3 Entity–Relationship Diagram
Figure 1: Entity-Relationship Diagram for MoneyMinder System
ERD Relationship Notes: The diagram illustrates the following cardinalities between entities:
• Users have a one-to-many relationship with: Accounts, Categories, Budgets, Recurring Payments, and Trans-
actions.
• Accounts have a one-to-many relationship with Transactions.
• Categories have a one-to-many relationship with: Budgets and Transactions.
• Groups have a one-to-many relationship with Transactions.
• Recurring Payments have a one-to-many relationship with Transactions.
• Users and Groups have a many-to-many relationship through the User Groups logic (Users join Groups).
1.4 Normalization Proof (Up to 3NF)
This section provides a detailed normalization proof for the MoneyMinder database schema, demonstrating compliance
with First (1NF), Second (2NF), and Third Normal Form (3NF).
COMP3030 - Fall 2025 3/13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
1.4.1 First Normal Form (1NF)
Requirement: All attributes must be atomic (no multi-valued attributes or repeating groups), and each table must
have a primary key.
Analysis:
• Atomic Attributes: Every attribute in all tables contains only atomic values.
– User Groups: We do not store a list of users (e.g., ”1, 2, 3”) in a single Group row. Instead, we use a
separate junction table where each row represents one user-group link.
– Transactions: The amount and original amount are single decimal values.
• Primary Keys:
– Single-column PKs: Users(user id), Accounts(account id), Transactions(transaction id).
– Composite PK: User Groups(user id, group id) identifies the unique membership of a user in a group.
Conclusion: All tables have primary keys and atomic attributes. The schema satisfies 1NF.
1.4.2 Second Normal Form (2NF)
Requirement: The schema must satisfy 1NF, and all non-key attributes must depend on the entire primary key (no
partial dependencies).
Analysis:
• Tables with Single-Column PKs: (e.g., Users, Accounts, Transactions)
All non-key attributes naturally depend on the single primary key. For example, in Transactions, amount and
date describe the specific transaction ID.
• Table with Composite Key: User Groups(user id, group id)
The non-key attribute is joined at.
Analysis: A ”join date” depends on both the specific User and the specific Group. It does not depend on the
User alone (they join different groups at different times) nor the Group alone.
Example: joined at = ’2025-01-01’ makes sense only when referring to User A joining Group B.
Conclusion: There are no partial dependencies; every non-key attribute depends on the full key. The schema satisfies
2NF.
1.4.3 Third Normal Form (3NF)
Requirement: The schema must satisfy 2NF and have no transitive dependencies. (Non-key attributes should not
depend on other non-key attributes).
Analysis:
• Transactions Table:
Attributes like amount, date, description depend directly on transaction id. We store account id (Foreign
Key) but not account name or account type. To get the account name, we join with the Accounts table. This
avoids transitive dependency.
Note on Exchange Rates: We store exchange rate in Transactions. While exchange rates are generally global
data, in a financial ledger, the ”rate applied” is a property of the transaction event (a snapshot in time), not
a dependency on a generic currency table. This is a correct design choice that preserves 3NF in the context of
historical records.
• Recurring Payments Table:
frequency and next due date depend on recurring id. We do not store User details (like email) here; we only
reference user id.
Conclusion: No transitive dependencies exist in any table. The schema satisfies 3NF.
COMP3030 - Fall 2025 4/13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
2 Physical Schema Definition
Figure 2
2.1 Complete DDL Scripts
-- 1. Users: Stores credentials and global settings
CREATE TABLE Users (
user_id INT PRIMARY KEY AUTO_INCREMENT,
username VARCHAR(50) NOT NULL,
email VARCHAR(100) UNIQUE NOT NULL,
password_hash VARCHAR(255) NOT NULL,
base_currency VARCHAR(3) DEFAULT ’VND’, -- e.g., VND, USD
COMP3030 - Fall 2025 5/13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 2. Groups: For shared expenses (Family, Trip, Roommates)
CREATE TABLE ‘Groups‘ (
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
FOREIGN KEY (group_id) REFERENCES ‘Groups‘(group_id) ON DELETE CASCADE
);
-- 4. Accounts: Wallets, Banks, etc.
CREATE TABLE Accounts (
account_id INT PRIMARY KEY AUTO_INCREMENT,
user_id INT NOT NULL,
account_name VARCHAR(50) NOT NULL,
-- FIXED: Changed to ENUM for consistency and safety
account_type ENUM(’Cash’, ’Bank Account’, ’Credit Card’, ’E-Wallet’, ’Investment’) NOT NULL,
balance DECIMAL(15, 2) DEFAULT 0.00,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);
-- 5. Categories: Spending types (System default or User custom)
CREATE TABLE Categories (
category_id INT PRIMARY KEY AUTO_INCREMENT,
user_id INT DEFAULT NULL, -- NULL = System Default (Global), NOT NULL = Custom User Category
category_name VARCHAR(50) NOT NULL,
type ENUM(’Income’, ’Expense’) NOT NULL,
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
COMP3030 - Fall 2025 6/13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
CREATE TABLE Recurring_Payments (
recurring_id INT PRIMARY KEY AUTO_INCREMENT,
user_id INT NOT NULL,
account_id INT NOT NULL,
category_id INT NOT NULL,
amount DECIMAL(15, 2) NOT NULL,
frequency ENUM(’Daily’, ’Weekly’, ’Monthly’, ’Yearly’) NOT NULL,
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
original_amount DECIMAL(15, 2), -- For Multi-Currency support
currency_code VARCHAR(3) DEFAULT ’VND’,
exchange_rate DECIMAL(10, 6) DEFAULT 1.0,
transaction_date DATETIME NOT NULL,
description TEXT,
FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
FOREIGN KEY (account_id) REFERENCES Accounts(account_id) ON DELETE CASCADE,
FOREIGN KEY (category_id) REFERENCES Categories(category_id),
FOREIGN KEY (group_id) REFERENCES ‘Groups‘(group_id) ON DELETE SET NULL,
FOREIGN KEY (recurring_id) REFERENCES Recurring_Payments(recurring_id) ON DELETE SET NULL
);
2.2 Definitions of Views, Indexes, and Partitioning Strategy
2.2.1 Views
Views simplify complex queries, provide abstracted data access, and support the specific reporting needs of the
MoneyMinder system (specifically for alerts and financial dashboards). Below are four essential views:
1. Unusual Spending Alert View Purpose: Pre-calculates the rolling average and maximum spending per
category for each user over the last 6 months.
Use Case: The backend system queries this view before inserting a new transaction. If the new transaction amount
exceeds average spent × 1.25, the system triggers an ”Unusual Spending” alert.
CREATE VIEW view_category_alert_stats AS
SELECT
user_id,
category_id,
AVG(amount) AS average_spent,
COMP3030 - Fall 2025 7/13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
MAX(amount) AS max_spent,
STDDEV(amount) AS spending_variability
FROM Transactions
WHERE transaction_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
GROUP BY user_id, category_id;
Example: SELECT average spent FROM view category alert stats WHERE user id = 101 AND category id = 5;
2. Monthly Financial Dashboard View Purpose: Aggregates total income and expenses per month, broken
down by category.
Use Case: Populates the main dashboard charts without requiring the frontend to process thousands of raw trans-
action rows.
CREATE VIEW view_monthly_dashboard AS
SELECT
t.user_id,
DATE_FORMAT(t.transaction_date, ’%Y-%m’) AS month_year,
c.category_name,
c.type AS transaction_type,
SUM(t.amount) AS total_amount
FROM Transactions t
JOIN Categories c ON t.category_id = c.category_id
GROUP BY t.user_id, month_year, c.category_name, c.type;
3. Group Expense Summary View Purpose: Calculates the total contribution of each member within shared
groups.
Use Case: Displayed on the ”Group Details” page to show who has spent the most and to help settle debts between
roommates or travel companions.
CREATE VIEW view_group_expense_summary AS
SELECT
t.group_id,
g.group_name,
u.username,
SUM(t.amount) AS total_contributed
FROM Transactions t
JOIN Users u ON t.user_id = u.user_id
JOIN ‘Groups‘ g ON t.group_id = g.group_id
WHERE t.group_id IS NOT NULL
GROUP BY t.group_id, g.group_name, u.username;
4. Upcoming Recurring Payments View Purpose: Identifies active subscriptions that are due for payment
within the next 7 days.
Use Case: Displayed as a ”Upcoming Bills” notification widget on the user’s home screen.
CREATE VIEW view_upcoming_payments AS
SELECT
r.user_id,
r.amount,
c.category_name,
r.next_due_date,
DATEDIFF(r.next_due_date, CURDATE()) AS days_until_due
FROM Recurring_Payments r
JOIN Categories c ON r.category_id = c.category_id
WHERE r.is_active = TRUE
AND r.next_due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY);
COMP3030 - Fall 2025 8/13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
2.2.2 Indexes
Indexes are critical for meeting the non-functional requirement of Performance, ensuring queries return in under 2
seconds even as transaction history grows.
• 1. Users Email Index
CREATE INDEX idx_users_email ON Users(email);
Rationale: The system uses email for authentication. This index ensures O(1) lookup speed during the login
process, preventing table scans.
• 2. Transactions Date Index
CREATE INDEX idx_transactions_date ON Transactions(transaction_date);
Rationale: Financial reports almost always filter by time (e.g., ”This Month”, ”Last Year”). This index
optimizes range queries on dates.
• 3. User History Composite Index
CREATE INDEX idx_transactions_user_date ON Transactions(user_id, transaction_date);
Rationale: The most common query is ”Show me my transactions sorted by date.” A composite index allows
the database to filter by user and sort by date in a single operation.
• 4. Alert Calculation Index
CREATE INDEX idx_transactions_alert ON Transactions(user_id, category_id, amount);
Rationale: Specifically designed to speed up the view category alert stats. It allows the database to
compute averages using a ”Covering Index” strategy.
• 5. Budget Lookup Index
CREATE INDEX idx_budgets_active ON Budgets(user_id, end_date);
Rationale: Ensures fast checking of whether a user has an active budget for the current period every time a
transaction is added.
2.2.3 Partitioning Strategy
As financial data grows indefinitely (users effectively never delete history), the Transactions table will become the
largest table in the database.
Transactions Table Strategy: Range Partitioning by Year.
ALTER TABLE Transactions
PARTITION BY RANGE (YEAR(transaction_date)) (
PARTITION p_old VALUES LESS THAN (2024),
PARTITION p_2024 VALUES LESS THAN (2025),
PARTITION p_2025 VALUES LESS THAN (2026),
PARTITION p_2026 VALUES LESS THAN (2027),
PARTITION p_future VALUES LESS THAN MAXVALUE
);
Rationale:
COMP3030 - Fall 2025 9/13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
• Query Pattern: Users rarely access detailed transaction history older than one year. 95% of queries (Dash-
board, Alerts, Budgets) focus on the current month or year.
• Performance: Partitioning ensures that current-year queries only scan the p 2025 partition, ignoring millions
of rows of historical data in p old or p 2024.
• Maintenance: Allows for efficient archiving of old financial data if necessary.
3 Task Division & Project Plan
3.1 Breakdown of Team Member Responsibilities
Team Member
Nguyen Son Giang
Tran Nam Nhat Anh
Nguyen Tran Nhat Minh
Nguyen Hoang Nam
Table 1: Team Member
The responsibilities of team members in the MoneyMinder – Personal Finance Management System project are clearly
divided to ensure efficient development, accountability, and smooth collaboration. Below is a detailed breakdown of
tasks assigned to each team member.
Nguyen Son Giang & Nguyen Tran Nhat Minh (Conceptual & Logical Design)
Requirements Analysis & Database Design
• Analyzed functional and non-functional requirements for the MoneyMinder system.
• Designed the conceptual and logical database schema covering Users, Groups, Accounts, Transactions, Cate-
gories, Budgets, and Recurring Payments.
• Constructed the ER Diagram representing relationships between personal and group transactions.
• Ensured database normalization up to Third Normal Form (3NF) to eliminate redundancy and maintain consis-
tency.
• Reviewed and refined the design to support multi-currency transactions, recurring payments, and unusual spend-
ing alerts.
Nguyen Son Giang & Tran Nam Nhat Anh (Physical Schema Definition)
Database Schema & DDL Implementation
• Implemented complete SQL DDL scripts, including table definitions, primary keys, foreign keys, constraints,
and ENUM types.
• Defined appropriate ON DELETE behaviors to preserve financial history and enforce referential integrity.
Triggers, Stored Procedures & Views
• Implemented database-side logic (triggers and procedures) to support recurring payment generation and alert-
related processing.
• Designed SQL views to support reporting features, including monthly spending dashboards, group expense
summaries, and alert statistics.
• Created indexing strategies to optimize query performance for analytics and historical reports.
COMP3030 - Fall 2025 10/13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
Tran Nam Nhat Anh & Nguyen Hoang Nam (Web Integration & System Implementation)
Backend API Development
• Implemented backend APIs that interact directly with the MoneyMinder database.
• Developed CRUD APIs for transactions (personal and group), categories, accounts, and recurring payments.
• Implemented business logic for multi-currency transactions, including exchange rate storage and base-currency
normalization.
• Developed backend logic to support automated recurring payments and unusual spending alerts.
Database Integration & Security
• Configured secure database connections and enforced the use of parameterized queries to prevent SQL injection.
• Implemented backend logic to support authentication, password hashing, and proper data isolation between
users and groups.
All Members (Testing, Optimization & Finalization)
Testing & Validation
• Designed and executed end-to-end test cases covering multi-currency transactions, recurring payments, group
expenses, and unusual spending alerts.
• Validated the correctness of financial calculations and database constraints.
• Tested system behavior under realistic transaction volumes to ensure reliability.
Performance Tuning & Documentation
• Performed query performance testing and index validation for reporting and alert-related queries.
• Prepared project documentation, including task division, system workflow descriptions, and testing results.
• Contributed to the final project report, presentation slides, and project demonstration.
3.2 Timeline/Gantt Chart
The timeline below illustrates the planned deliverables for Activities 1–5, ranging from Requirements Analysis to Final
Submission.
COMP3030 - Fall 2025 11/13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
Figure 3: Project Timeline and Gantt Chart (Dec 1 - Dec 22)
4 Supporting Documentation
4.1 Design Rationale
Our database design prioritizes financial accuracy, automation capabilities, and query performance to support the
functional requirements of the MoneyMinder system.
• Normalization (3NF): The schema is strictly normalized to Third Normal Form to prevent data redundancy
and anomalies. Entities such as Users, Accounts, Categories, and Groups are separated into distinct tables.
Specific Decision: We separated Recurring Payments from Transactions. A recurring payment is a ”rule”
(schedule), while a transaction is an ”event” (history). This separation allows users to modify a future schedule
without altering historical financial records.
• Primary & Foreign Keys: Auto-incrementing INT primary keys (e.g., transaction id) are used for efficient
indexing and joining.
Referential Integrity Strategy: We utilize specific ON DELETE actions to handle data lifecycle:
– CASCADE on Users: If a user deletes their account, all sensitive financial data is instantly wiped for
privacy compliance.
– SET NULL on Recurring Payments: If a user deletes a subscription rule, the historical transactions
generated by that rule remain in the Transactions table (with recurring id becoming NULL) to preserve
accurate financial history.
• Data Types & Constraints:
– Financial Precision: We use DECIMAL(15, 2) for all monetary fields instead of FLOAT. This is critical
for financial applications to avoid floating-point rounding errors.
– Enumerated Types: We employ ENUM for account type and category.type. This enforces data consis-
tency at the database level.
– Multi-Currency Support: The Transactions table includes both amount (normalized base currency) and
original amount + currency code. This allows the system to store the exact details of a foreign expense
(e.g., ”50 USD”) while simultaneously allowing for standardized reporting in the user’s home currency.
COMP3030 - Fall 2025 12/13
College of Engineering and Computer Science
Database and database systems
December 15, 2025
• Logic Optimization (Unusual Spending Alerts): To address performance concerns, we implemented the
View Category Alert Stats. Instead of calculating averages on-the-fly during every transaction insert (which
is computationally expensive), the system queries this optimized view to compare the new bill against a rolling
6-month average.
4.2 Sample Data Loading Approach
We will populate the database using SQL INSERT scripts to simulate realistic financial scenarios and demonstrate
the system’s core features.
Scripting Order: The scripts respect foreign key dependencies to ensure successful insertion:
1. Base Data: Users, Groups, Categories (System Defaults).
2. Financial Setup: Accounts (Wallets, Banks), Budgets.
3. Automation Rules: Recurring Payments (Subscriptions).
4. History: Transactions (linked to all above).
Example Script Snippet:
-- 1. Create a User and their Account
INSERT INTO Users (username, email, password_hash, base_currency)
VALUES (’Nguyen Van A’, ’a.nguyen@example.com’, ’hashed_pw_123’, ’VND’);
INSERT INTO Accounts (user_id, account_name, account_type, balance)
VALUES (1, ’Vietcombank Main’, ’Bank Account’, 50000000.00);
-- 2. Create a Recurring Subscription (Netflix)
INSERT INTO Recurring_Payments (user_id, account_id, category_id,
amount, frequency, next_due_date)
VALUES (1, 1, 5, 260000.00, ’Monthly’, ’2025-12-20’);
-- 3. Insert a Transaction (Simulating a foreign currency payment)
INSERT INTO Transactions (user_id, account_id, category_id, amount,
original_amount, currency_code,
exchange_rate, description)
VALUES (1, 1, 2, 2500000.00, 100.00, ’USD’, 25000.00, ’Travel Souvenirs’);
COMP3030 - Fall 2025 13/13
Assignment Final submission & presentation slide

Due soon - 1 day left