# MoneyMinder Backend

Backend API for MoneyMinder Personal Finance Management System.

## Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. **Initialize Database**
```bash
# Run the SQL scripts in order:
mysql -u root -p < ../Physical_Schema_Definition.sql
mysql -u root -p < ../Sample_Data.sql
```

4. **Run the Server**
```bash
python app.py
```

The API will be available at `http://localhost:5000`

5. **Optional: Start Recurring Worker**
```bash
python recurring_worker.py  # polls every 60s by default; override with RECURRING_POLL_SECONDS
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user (requires auth)

### Accounts
- `GET /api/accounts` - List all accounts
- `POST /api/accounts` - Create new account
- `GET /api/accounts/<id>` - Get specific account
- `PUT /api/accounts/<id>` - Update account
- `DELETE /api/accounts/<id>` - Delete account
- `GET /api/accounts/summary` - Get accounts summary

### Transactions
- `GET /api/transactions` - List transactions (with filters)
- `POST /api/transactions` - Create transaction
- `GET /api/transactions/<id>` - Get specific transaction
- `PUT /api/transactions/<id>` - Update transaction
- `DELETE /api/transactions/<id>` - Delete transaction

### Categories
- `GET /api/categories` - List all categories
- `POST /api/categories` - Create custom category
- `GET /api/categories/<id>` - Get specific category
- `PUT /api/categories/<id>` - Update category
- `DELETE /api/categories/<id>` - Delete category

### Analytics
- `GET /api/analytics/dashboard` - Dashboard overview
- `GET /api/analytics/monthly-report` - Monthly report
- `GET /api/analytics/spending-by-category` - Category breakdown
- `GET /api/analytics/trends` - Spending trends
- `GET /api/analytics/budget-status` - Budget tracking
- `GET /api/analytics/unusual-spending` - Unusual spending alerts

## Authentication

All endpoints except `/api/auth/register` and `/api/auth/login` require authentication.

Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Sample Request

```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"Test@2024","base_currency":"VND"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@2024"}'

# Get accounts (with token)
curl -X GET http://localhost:5000/api/accounts \
  -H "Authorization: Bearer <your_token>"
```

## Database Features

- **2 Stored Procedures**: Recurring payments & budget alerts
- **3 Triggers**: Automatic account balance updates
- **2 Views**: Monthly reports & unusual spending detection
- **Security**: Role-based access, encrypted passwords
- **Indexes**: Optimized query performance

## Tech Stack

- Flask 3.0
- PyMySQL
- JWT Authentication
- bcrypt for password hashing
