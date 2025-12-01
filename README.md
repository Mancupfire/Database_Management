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
4.  **Multi-Currency & Travel Mode (NEW FEATURE):**
    * Allows recording transactions in foreign currencies different from the base currency (e.g., spending USD while traveling when the main account is in VND).
    * The user enters the original currency amount and the exchange rate at the time of the transaction. The system stores both and converts to the base currency for reporting.
5.  **Subscription & Recurring Payments (NEW FEATURE):**
    * Users define recurring expenses (e.g., Netflix, Rent, Internet) with a specific frequency (monthly, yearly).
    * The system automatically generates the transaction when due or sends a notification reminding the user to confirm the payment.
6.  **Unusual Spending Alerts (NEW FEATURE):**
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

* **Database:** [MySQL / PostgreSQL] - *Please select the one you are using*
* **Backend:** [Python (Flask) / Node.js / PHP] - *Please select the stack you are using*
* **Frontend:** [HTML5, CSS3, Bootstrap / React] - *Please select the stack you are using*
* **Version Control:** Git & GitHub
* **Diagramming Tools:** [Draw.io / Lucidchart] (for ER Diagrams)

## 👥 Team Roles and Responsibilities

*(Adjust this table to match your team's actual reality)*

| Name | Role | Responsibilities |
| :--- | :--- | :--- |
| **Nguyen Son Giang** | Project Lead & DB Architect | ERD design, DB schema normalization (including the new `Recurring_Payments` table and currency fields). |
| **Tran Nam Nhat Anh** | Backend Developer | Developing CRUD APIs, handling multi-currency transaction logic, and the automated scheduler for recurring payments. |
| **Nguyen Tran Nhat Minh** | Frontend Developer | UI/UX design, creating input forms that support foreign currency selection and subscription management interfaces. |
| **Nguyen Hoang Nam** | QA & Documentation | Functional testing (especially exchange rate calculations and unusual alerts logic), writing documentation. |

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
