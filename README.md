# Database_Management

# 📌 MoneyMinder: Personal Finance Management System

## 📄 Brief Description
**MoneyMinder** is a comprehensive database-driven application designed to help individuals track their income, expenses, and savings goals. 

**The Problem:** Many individuals struggle to maintain financial health due to scattered data across various bank accounts and cash transactions, leading to a lack of visibility into spending habits and difficulty in adhering to budgets.

**The Solution:** This system solves this problem by providing a centralized platform to record financial transactions, categorize spending, and visualize financial health through generated reports. It leverages a relational database to ensure data integrity and allow for complex querying of financial history.

## 🎯 Functional & Non-functional Requirements

### Functional Requirements
1.  **User Management:** Users can register, login, and manage their profiles securely.
2.  **Transaction Management:** Users can Create, Read, Update, and Delete (CRUD) income and expense records.
3.  **Categorization:** Transactions must be linked to specific categories (e.g., Groceries, Rent, Salary).
4.  **Budgeting:** Users can set monthly budget limits for specific categories and receive alerts when nearing limits.
5.  **Reporting:** The system generates monthly financial summaries and visualizes spending distribution.

### Non-functional Requirements
1.  **Data Integrity:** The database must strictly enforce referential integrity (foreign keys) and ACID properties for all transactions.
2.  **Security:** User passwords must be hashed; SQL injection prevention measures must be implemented.
3.  **Performance:** Queries for transaction history should execute in under 2 seconds for datasets up to 10,000 records.
4.  **Scalability:** The database schema should support the future addition of features like "Recurring Transactions" without major restructuring.

## 🧱 Planned Core Entities
*Brief outline of the database schema:*

1.  **Users:** Stores user credentials and profile information.
2.  **Accounts:** Represents different fund sources (e.g., Cash, Bank Account, Credit Card).
3.  **Categories:** Defines types of spending/income (e.g., Food, Utilities, Salary) to allow for grouping in reports.
4.  **Transactions:** The central fact table recording the amount, date, description, type (income/expense), and links to User, Account, and Category.
5.  **Budgets:** Stores the spending limits set by a user for a specific category within a specific time frame.

## 🔧 Tech Stack

* **Database:** [MySQL / PostgreSQL]
* **Backend:** [Python (Flask) / Node.js / PHP]
* **Frontend:** [HTML5, CSS3, Bootstrap / React]
* **Version Control:** Git & GitHub
* **Diagramming Tools:** [Draw.io / Lucidchart] (for ER Diagrams)

## 👥 Team Members and Roles

| Name | Role | Responsibilities |
| :--- | :--- | :--- |
| **[Member 1 Name]** | Project Lead & DB Architect | Database design (ERD), normalization, and schema implementation. |
| **[Member 2 Name]** | Backend Developer | API development, SQL query optimization, and server-side logic. |
| **[Member 3 Name]** | Frontend Developer | UI/UX design, creating forms, and visualizing data charts. |
| **[Member 4 Name]** | QA & Documentation | Testing, bug tracking, and compiling the final report/README. |

## 🗓️ Timeline (Planned Milestones)

* **Week 1: Requirement Analysis & Design**
    * Define project scope.
    * Finalize ER Diagram and database normalization.
* **Week 2: Database Implementation**
    * Set up the DBMS.
    * Write DDL scripts to create tables, constraints, and relationships.
* **Week 3: Backend Development**
    * Connect application to the database.
    * Implement CRUD logic and basic authentication.
* **Week 4: Frontend & Integration**
    * Build user interface.
    * Integrate frontend with backend APIs.
* **Week 5: Testing & Deployment**
    * Perform functional testing and edge-case validation.
    * Finalize documentation and project submission.
