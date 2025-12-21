# 📌 MoneyMinder: Personal Finance Management System

## 👥 Team Members
- Nguyen Son Giang
- Tran Nam Nhat Anh
- Nguyen Tran Nhat Minh
- Nguyen Hoang Nam

## 📄 Brief Description
**MoneyMinder** is a comprehensive database-driven application designed to help individuals **and groups (families, roommates)** track their income, expenses, and savings goals intelligently and flexibly.

**The Problem:** Many individuals struggle to maintain financial health due to scattered data. They find it difficult to track shared expenses within a group, often forget recurring payments (subscriptions), get confused when dealing with multiple currencies while traveling abroad, and fail to timely notice when a bill (e.g., electricity, water) increases abnormally.

**The Solution:** This system solves these problems by providing a centralized platform to record financial transactions **(personal and shared)**. It supports **multi-currency** for travel, automates **recurring payments**, and proactively **alerts** users to signs of unusual spending. It leverages a robust relational database to ensure data integrity and allow for complex querying of financial history.

## 🎯 Functional & Non-functional Requirements

### Functional Requirements

1.  **User Management:** Users can register, login, and set up their profiles (including selecting a default base currency, e.g., VND or USD).
2.  **Group Management:** Users can create shared spending groups, invite members, and view member lists.
3.  **Transaction Management:** CRUD (Create, Read, Update, Delete) income/expense records. Users select a "Personal" or "Group" context khi creating a transaction.
4.  **Multi-Currency & Travel Mode:**
    * Allows recording transactions in foreign currencies different from the base currency (e.g., spending USD while traveling when the main account is in VND).
    * The user enters the original currency amount and the exchange rate at the time of the transaction. The system stores both and converts to the base currency for reporting.
5.  **Subscription & Recurring Payments:**
    * Users define recurring expenses (e.g., Netflix, Rent, Internet) with a specific frequency (monthly, yearly).
    * The system automatically generates the transaction when due or sends a notification reminding the user to confirm the payment.
6.  **Unusual Spending Alerts:**
    * The system analyzes spending history for essential categories (e.g., Electricity, Water).
    * If a newly entered bill is significantly higher than that user's historical average (e.g., exceeds by 25%), the system displays an alert for the user to review.
7.  **Categorization & Budgeting:** Link transactions to specific categories and set monthly spending limits.
8.  **Reporting:** Generate comprehensive financial reports, filterable by time period, category, group member, or currency type.

### Non-functional Requirements
1.  **Data Integrity:** The database must strictly enforce referential integrity (foreign keys) and ACID properties.
2.  **Security:** User passwords must be hashed; SQL injection prevention measures must be implemented. Ensure data privacy between different groups and individuals.
3.  **Performance:** Historical queries and report calculations must be fast, even as transaction data grows over time.
4.  **Scalability:** The DB schema should be designed to easily support future features (e.g., integrating an automatic exchange rate API later on).

## 🔄 System Workflow

The diagram below illustrates the high-level user flow within the MoneyMinder system.

*(Note: The workflow below is basic. New features like "Select Currency" will appear during the "Add Transaction" step. The "Recurring Payments" feature will be a background process that automatically creates transactions).*

![Personal Financial Management System Workflow](https://github.com/Mancupfire/Database_Management/blob/main/Image/Workflow.png)

## 🧱 Planned Core Entities
*Database Schema Outline:*

1.  **Users:** Stores credentials, profile information, and **`base_currency` (default currency)**.
2.  **Groups & User_Groups:** Manages group information and group membership relationships.
3.  **Accounts:** Represents fund sources (e.g., Cash, Bank Account, Credit Card).
4.  **Categories:** Defines types of spending/income.
5.  **Transactions:** The central fact table.
    * Existing fields: amount, date, description, type, UserID, AccountID, CategoryID, GroupID (nullable).
    * **New fields for Multi-Currency:** `original_amount` (foreign currency amount), `currency_code` (foreign currency type, e.g., USD), `exchange_rate` (applied rate).
6.  **Recurring_Payments:** Stores definitions for repeating expenses.
    * Fields: `frequency` (e.g., monthly/weekly), `start_date`, `next_due_date`, estimated amount, and foreign keys linking to User and Category.
7.  **Budgets:** Stores spending limits set by a user for specific categories.

## 🔧 Tech Stack

* **Database:** MySQL 8.0+
* **Backend:** Python 3.8+ with Flask framework
* **Frontend:** HTML5, CSS3, Bootstrap 5, Vanilla JavaScript
* **Authentication:** JWT (JSON Web Tokens)
* **Version Control:** Git & GitHub
* **Diagramming Tools:** Draw.io (for ER Diagrams)

## 👥 Team Roles and Responsibilities

| Name | Role | Responsibilities |
| :--- | :--- | :--- |
| **Nguyen Son Giang** | Project Lead & DB Architect | ERD design, DB schema normalization, stored procedures, triggers, and security setup. |
| **Tran Nam Nhat Anh** | Backend Developer | Flask API development, CRUD operations, authentication system, and business logic implementation. |
| **Nguyen Tran Nhat Minh** | Frontend Developer | UI/UX design, responsive web interface, form handling, and data visualization. |
| **Nguyen Hoang Nam** | QA & Documentation | Testing all features, API documentation, user guide, and presentation materials. |

## 🚀 Quick Start

### Prerequisites
- MySQL 8.0 or higher
- Python 3.8 or higher
- Web browser (Chrome, Firefox, Safari, or Edge)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Mancupfire/VinUni-database-project-MoneyMinder.git
cd Database_Project
```

2. **Run setup script**
```bash
chmod +x setup.sh
./setup.sh
```

3. **Configure environment** (if needed)
```bash
# Edit backend/.env with your database credentials
nano backend/.env
```

4. **Start the application**
```bash
chmod +x run.sh
./run.sh
```

5. **Access the application**
- Frontend: http://localhost:8080
- Backend API: http://localhost:5000

### Demo Account
```
Email: john.doe@example.com
Password: Demo@2024
```

## 📁 Project Structure

```
Database_Project/
├── Physical_Schema_Definition.sql  # Database schema with procedures & triggers
├── Sample_Data.sql                 # Test data for demo
├── setup.sh                        # Setup script
├── run.sh                          # Run script
├── README.md                       # This file
├── backend/                        # Flask API
│   ├── app.py                      # Main application
│   ├── config.py                   # Configuration
│   ├── database.py                 # Database connection
│   ├── auth.py                     # Authentication utilities
│   ├── routes_*.py                 # API endpoints
│   ├── requirements.txt            # Python dependencies
│   └── .env.example                # Environment template
└── frontend/                       # Web interface
    ├── index.html                  # Main HTML file
    ├── css/
    │   └── style.css               # Custom styles
    └── js/
        └── app.js                  # Frontend logic
```

## ✨ Features Implemented

### Database Layer
- ✅ **8 Tables**: Users, Groups, User_Groups, Accounts, Categories, Budgets, Recurring_Payments, Transactions
- ✅ **2 Stored Procedures**: Auto-create recurring transactions, check budget alerts
- ✅ **3 Triggers**: Auto-update account balances on transaction insert/update/delete
- ✅ **2 Views**: Monthly reports, unusual spending detection
- ✅ **5 Indexes**: Optimized for common queries
- ✅ **Security**: Role-based MySQL users (Admin, App, Read-only)
- ✅ **Normalization**: 3NF compliant schema

### Backend API (Flask)
- ✅ **Authentication**: JWT-based login/register
- ✅ **Accounts CRUD**: Create, read, update, delete accounts
- ✅ **Transactions CRUD**: Full transaction management
- ✅ **Categories Management**: System & custom categories
- ✅ **Analytics**: Dashboard, reports, spending trends, budget tracking
- ✅ **Unusual Spending Detection**: Automatic alerts for abnormal expenses

### Frontend (Web Interface)
- ✅ **Responsive Design**: Bootstrap 5 with mobile support
- ✅ **Dashboard**: Overview of finances with summary cards
- ✅ **Transaction Management**: Add, view, filter, delete transactions
- ✅ **Account Management**: Manage multiple accounts
- ✅ **Budget Management**: Create, monitor, and track spending limits
- ✅ **Group Expenses**: Create groups, add members, track shared expenses
- ✅ **Recurring Payments**: Manage subscriptions and auto-payments
- ✅ **Analytics**: Visual budget tracking and spending breakdown
- ✅ **Real-time Alerts**: Toast notifications for actions

## 📊 Database Features Showcase

### 1. Stored Procedure: Auto-Recurring Payments
```sql
CALL SP_Create_Recurring_Transaction(1);
-- Automatically creates transaction and updates next due date
```

### 2. Stored Procedure: Budget Alert Check
```sql
CALL SP_Check_Budget_Alert(1, 1, '2024-03-01', '2024-03-31', @limit, @spent, @percentage, @status);
-- Returns budget status: SAFE, NORMAL, WARNING, or EXCEEDED
```

### 3. Triggers: Auto-Balance Update
```sql
INSERT INTO Transactions (...);
-- Automatically updates account balance via trigger
```

### 4. View: Monthly Report
```sql
SELECT * FROM View_Monthly_Report WHERE user_id = 1;
-- Pre-aggregated monthly spending by category
```

### 5. View: Unusual Spending Detection
```sql
SELECT * FROM View_Category_Alert_Stats WHERE user_id = 1;
-- 6-month average for anomaly detection
```

## 🔒 Security Features

1. **Password Hashing**: SHA256 for stored passwords
2. **JWT Authentication**: Secure token-based auth
3. **SQL Injection Prevention**: Parameterized queries
4. **Role-Based Access**: MySQL users with least privilege (rotate credentials in `.env` and `Physical_Schema_Definition.sql` before deployment)
5. **CORS Protection**: Restrict via `FRONTEND_ORIGINS` env (default `http://localhost:8080`)

## 📈 Performance Optimizations

1. **Indexes**: Strategic indexing on frequently queried columns
2. **Views**: Pre-computed aggregations for reports
3. **Connection Pooling**: Efficient database connections
4. **Query Optimization**: Minimized N+1 queries

## 🧪 Testing

### Manual Testing Checklist
- [ ] User registration and login
- [ ] Create/edit/delete accounts
- [ ] Add transactions (income & expense)
- [ ] View dashboard with correct calculations
- [ ] Filter transactions by date/account
- [ ] Budget tracking displays correctly
- [ ] Unusual spending alerts trigger
- [ ] Account balance updates automatically

### API Testing with cURL
```bash
# Health check
curl http://localhost:5000/api/health

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john.doe@example.com","password":"Demo@2024"}'

# Get accounts (replace TOKEN)
curl http://localhost:5000/api/accounts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 📝 API Documentation

Full API documentation available at: [Backend README](backend/README.md)

### Main Endpoints
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/accounts` - List accounts
- `POST /api/transactions` - Create transaction
- `GET /api/analytics/dashboard` - Dashboard data
- `GET /api/analytics/budget-status` - Budget tracking

## 🎓 Course Requirements Compliance

| Requirement | Status | Implementation |
|------------|--------|----------------|
| ≥4 entities | ✅ | 8 tables implemented |
| ERD & 3NF | ✅ | Properly normalized schema |
| ≥2 stored procedures | ✅ | 2 procedures (recurring payments, budget check) |
| ≥1 trigger | ✅ | 3 triggers (balance updates) |
| Indexing | ✅ | 5 strategic indexes |
| Security | ✅ | Role-based users, password hashing, JWT |
| Web interface | ✅ | Full-featured responsive UI |
| CRUD operations | ✅ | Complete for all entities |
| Analytics | ✅ | Dashboard, reports, trends |
| Documentation | ✅ | Comprehensive README & code comments |

## 🐛 Known Issues & Future Enhancements

### Current Limitations
- Group expense splitting not fully implemented
- Multi-currency exchange rate is manual (no API integration)
- Recurring payments scheduler is provided as a lightweight worker (`backend/recurring_worker.py`) but is not yet packaged as a service

### Planned Enhancements
- Automated recurring payment scheduler (cron job)
- Real-time currency exchange rate API
- Group expense calculator with debt settlement
- Export reports to PDF/CSV
- Email notifications for budget alerts
- Mobile app integration

## 🗓️ Timeline (Planned Milestones)

* **Week 1: Requirement Analysis & Design**
    * Finalize scope with new features (Multi-currency, Recurring, Alerts).
    * Finalize ER Diagram and database normalization.
* **Week 2: Database Implementation**
    * Set up DBMS. Write DDL scripts for all tables including the new `Recurring_Payments` and changes to `Transactions`.
* **Week 3: Backend Development - Core & Currency**
    * Implement basic CRUD and Authentication.
    * Implement logic for handling multi-currency transactions and exchange rate storage.
* **Week 4: Backend Development - Advanced Features**
    * Implement logic for the Recurring Payments scheduler background process.
    * Implement logic for Unusual Spending Alerts (comparing current bill vs historical average).
* **Week 5: Frontend Integration & Testing**
    * Build UI for transaction inputs (with currency formatting) and subscription management.
    * Perform comprehensive testing and final deployment.
