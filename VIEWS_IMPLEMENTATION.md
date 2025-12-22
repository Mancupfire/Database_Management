# Database Views Implementation

## Overview
Three advanced database views have been implemented to enhance the MoneyMinder application's analytical capabilities and notification system.

## Implemented Views

### 1. View_Unusual_Spending_Alert
**Purpose:** Pre-calculates the rolling average and maximum spending per category for each user over the last 6 months.

**Use Case:** The backend system queries this view before processing transactions. If a new transaction amount exceeds `average_spent × 1.25` (alert_threshold), the system triggers an "Unusual Spending" alert.

**Features:**
- Tracks spending patterns by user and category
- Calculates average, maximum, and standard deviation
- Sets alert threshold at 1.25x average
- Requires at least 3 transactions to establish a pattern
- Only monitors expense categories

**API Integration:**
- Used in: `backend/scheduler.py` → `check_unusual_spending()`
- Notifications created automatically every 6 hours

**Query Example:**
```sql
SELECT * FROM View_Unusual_Spending_Alert 
WHERE user_id = 1 AND category_id = 5;
```

---

### 2. View_Group_Expense_Summary
**Purpose:** Calculates the total contribution of each member within shared groups.

**Use Case:** Displayed on the "Group Details" page to show who has spent the most and to help settle debts between roommates or travel companions.

**Features:**
- Total expenses per member
- Total contributions per member
- Net spending calculation
- Fair share calculation (total expenses / member count)
- Balance owed (individual expenses - fair share)
- Transaction count per member

**API Endpoints:**
- `GET /api/groups/<group_id>/expense-summary` - Get full expense breakdown

**Use Cases:**
- Roommate expense splitting
- Travel group cost sharing
- Family budget tracking
- Debt settlement between members

**Query Example:**
```sql
SELECT * FROM View_Group_Expense_Summary 
WHERE group_id = 1
ORDER BY net_spending DESC;
```

---

### 3. View_Upcoming_Recurring_Payments
**Purpose:** Identifies active subscriptions that are due for payment within the next 7 days.

**Use Case:** Displayed as an "Upcoming Bills" notification widget on the user's home screen.

**Features:**
- Shows bills due within 7 days
- Calculates days until due
- Provides human-readable due status ("Due Today", "Due Tomorrow", "Due in X days")
- Assigns urgency levels (critical, high, medium, low)
- Includes full payment details (amount, category, account)

**Urgency Levels:**
- **Critical:** Overdue bills (days_until_due < 0)
- **High:** Due within 2 days
- **Medium:** Due within 3-5 days
- **Low:** Due within 6-7 days

**API Endpoints:**
- `GET /api/recurring/upcoming` - Get upcoming bills for current user

**API Integration:**
- Used in: `backend/scheduler.py` → `check_upcoming_bills()`
- Notifications created daily at 9:00 AM
- Dashboard widget displays upcoming bills

**Query Example:**
```sql
SELECT * FROM View_Upcoming_Recurring_Payments
WHERE user_id = 1 AND urgency_level IN ('critical', 'high')
ORDER BY next_due_date ASC;
```

---

## Database Schema Updates

All views have been added to `Physical_Schema_Definition.sql` and will be created automatically when running:
```bash
./setup.sh
```

## Backend Integration

### Scheduler Updates (backend/scheduler.py)
- `check_unusual_spending()` - Now uses `View_Unusual_Spending_Alert`
- `check_upcoming_bills()` - Now uses `View_Upcoming_Recurring_Payments`

### New API Endpoints

#### Groups
- `GET /api/groups/<group_id>/expense-summary`
  - Returns detailed expense breakdown for all group members
  - Shows who owes whom
  - Calculates fair share automatically

#### Recurring Payments
- `GET /api/recurring/upcoming`
  - Returns upcoming bills with urgency levels
  - Shows days until due
  - Provides human-readable status

## Frontend Integration

### Dashboard Enhancements
- **Notification Bell:** Real-time alerts for unusual spending and upcoming bills
- **Charts:** Monthly trend (6 months) and yearly summary visualization
- **Upcoming Bills Widget:** Shows bills due in next 7 days with urgency indicators

### Notifications System
- Unusual spending alerts (every 6 hours)
- Upcoming bill reminders (daily at 9 AM)
- Mark as read functionality
- Severity levels (info, warning, critical)

## Performance Considerations

All views are optimized with:
- Indexed foreign keys
- Date range filtering to limit data size
- Pre-calculated aggregations to reduce query complexity
- Efficient JOINs with proper table relationships

## Testing

To test the views:

1. **Unusual Spending:**
   ```sql
   -- Check alert thresholds
   SELECT * FROM View_Unusual_Spending_Alert WHERE user_id = 1;
   
   -- Create transaction exceeding threshold to trigger notification
   ```

2. **Group Expenses:**
   ```sql
   -- View group summary
   SELECT * FROM View_Group_Expense_Summary WHERE group_id = 1;
   ```

3. **Upcoming Bills:**
   ```sql
   -- Check upcoming bills
   SELECT * FROM View_Upcoming_Recurring_Payments WHERE user_id = 1;
   ```

## Future Enhancements

Potential additions:
- Email notifications for critical alerts
- SMS notifications for overdue bills
- Custom alert thresholds per category
- Spending trend predictions
- Budget vs. actual comparison view
- Investment portfolio tracking view

---

**Implementation Date:** December 22, 2025  
**Database:** MoneyMinder_DB  
**Status:** ✅ Active and Tested
