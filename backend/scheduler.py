"""
Background scheduler for recurring payments and notifications
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date
from database import Database
import logging

logger = logging.getLogger(__name__)

def process_due_recurring_payments():
    """Check and process recurring payments that are due"""
    try:
        # Get all active recurring payments that are due
        due_payments = Database.execute_query(
            """
            SELECT 
                r.recurring_id, r.user_id, r.account_id, r.category_id,
                r.amount, r.frequency, r.next_due_date
            FROM Recurring_Payments r
            WHERE r.is_active = TRUE 
            AND r.next_due_date <= CURDATE()
            """,
            fetch_all=True
        )
        
        if not due_payments:
            logger.info("No due recurring payments found")
            return
        
        logger.info(f"Processing {len(due_payments)} due recurring payments")
        
        for payment in due_payments:
            try:
                # Create transaction for this recurring payment
                Database.execute_query(
                    """
                    INSERT INTO Transactions 
                    (user_id, account_id, category_id, recurring_id, amount, 
                     transaction_date, description)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    """,
                    (
                        payment['user_id'],
                        payment['account_id'],
                        payment['category_id'],
                        payment['recurring_id'],
                        payment['amount'],
                        f"Recurring payment - {payment['frequency']}"
                    ),
                    commit=True
                )
                
                # Update next due date
                Database.execute_query(
                    """
                    UPDATE Recurring_Payments
                    SET next_due_date = CASE 
                        WHEN frequency = 'Daily' THEN DATE_ADD(next_due_date, INTERVAL 1 DAY)
                        WHEN frequency = 'Weekly' THEN DATE_ADD(next_due_date, INTERVAL 1 WEEK)
                        WHEN frequency = 'Monthly' THEN DATE_ADD(next_due_date, INTERVAL 1 MONTH)
                        WHEN frequency = 'Yearly' THEN DATE_ADD(next_due_date, INTERVAL 1 YEAR)
                    END
                    WHERE recurring_id = %s
                    """,
                    (payment['recurring_id'],),
                    commit=True
                )
                
                logger.info(f"Processed recurring payment ID {payment['recurring_id']}")
                
            except Exception as e:
                logger.error(f"Error processing recurring payment ID {payment['recurring_id']}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error in process_due_recurring_payments: {str(e)}")

def check_upcoming_bills():
    """Check for upcoming recurring bills in the next 3 days and create notifications"""
    try:
        # Use the new view for upcoming bills (filters for 7 days but we'll use all)
        upcoming = Database.execute_query(
            """
            SELECT 
                recurring_id, user_id, amount, next_due_date,
                email, username, category_name, days_until_due, due_status, urgency_level
            FROM View_Upcoming_Recurring_Payments
            WHERE days_until_due <= 3
            """,
            fetch_all=True
        )
        
        if upcoming:
            logger.info(f"Found {len(upcoming)} upcoming bills in next 3 days")
            
            for bill in upcoming:
                # Check if notification already exists for this bill today
                existing = Database.execute_query(
                    """
                    SELECT notification_id FROM Notifications
                    WHERE user_id = %s AND type = 'upcoming_bill' 
                    AND related_id = %s
                    AND DATE(created_at) = CURDATE()
                    """,
                    (bill['user_id'], bill['recurring_id']),
                    fetch_one=True
                )
                
                if not existing:
                    # Create notification
                    Database.execute_query(
                        """
                        INSERT INTO Notifications (user_id, type, title, message, severity, related_id)
                        VALUES (%s, 'upcoming_bill', %s, %s, 'info', %s)
                        """,
                        (
                            bill['user_id'],
                            'Upcoming Bill',
                            f"{bill['category_name']} payment of {bill['amount']} VND due on {bill['next_due_date']}",
                            bill['recurring_id']
                        ),
                        commit=True
                    )
                    logger.info(f"Created notification: {bill['category_name']} - ${bill['amount']} due on {bill['next_due_date']}")
        
    except Exception as e:
        logger.error(f"Error checking upcoming bills: {str(e)}")

def check_unusual_spending():
    """Check for unusual spending patterns and create notifications"""
    try:
        # Get users with recent transactions that exceed their average using the new view
        unusual = Database.execute_query(
            """
            SELECT 
                t.user_id, t.transaction_id, t.amount, 
                u.email, u.username,
                c.category_name, v.average_spent, v.alert_threshold
            FROM Transactions t
            JOIN Users u ON t.user_id = u.user_id
            JOIN Categories c ON t.category_id = c.category_id
            JOIN View_Unusual_Spending_Alert v ON t.user_id = v.user_id AND t.category_id = v.category_id
            WHERE t.transaction_date >= DATE_SUB(NOW(), INTERVAL 6 HOUR)
            AND t.amount > v.alert_threshold
            AND c.type = 'Expense'
            """,
            fetch_all=True
        )
        
        if unusual:
            logger.info(f"Found {len(unusual)} unusual spending transactions")
            
            for txn in unusual:
                # Check if notification already exists for this transaction
                existing = Database.execute_query(
                    """
                    SELECT notification_id FROM Notifications
                    WHERE user_id = %s AND type = 'unusual_spending' 
                    AND related_id = %s
                    """,
                    (txn['user_id'], txn['transaction_id']),
                    fetch_one=True
                )
                
                if not existing:
                    # Create notification
                    Database.execute_query(
                        """
                        INSERT INTO Notifications (user_id, type, title, message, severity, related_id)
                        VALUES (%s, 'unusual_spending', %s, %s, 'warning', %s)
                        """,
                        (
                            txn['user_id'],
                            'Unusual Spending Alert',
                            f"You spent {abs(txn['amount'])} VND on {txn['category_name']}, which is 50% more than your average of {abs(txn['average_spent'])} VND",
                            txn['transaction_id']
                        ),
                        commit=True
                    )
                    logger.warning(f"Created unusual spending notification: User {txn['username']} spent ${txn['amount']} on {txn['category_name']} (avg: ${txn['average_spent']})")
        
    except Exception as e:
        logger.error(f"Error checking unusual spending: {str(e)}")

# Initialize scheduler
scheduler = BackgroundScheduler()

def start_scheduler():
    """Start the background scheduler"""
    try:
        # Process recurring payments every day at 1 AM
        scheduler.add_job(
            process_due_recurring_payments,
            CronTrigger(hour=1, minute=0),
            id='process_recurring',
            name='Process due recurring payments',
            replace_existing=True
        )
        
        # Check upcoming bills every day at 9 AM
        scheduler.add_job(
            check_upcoming_bills,
            CronTrigger(hour=9, minute=0),
            id='upcoming_bills',
            name='Check upcoming bills',
            replace_existing=True
        )
        
        # Check unusual spending every 6 hours
        scheduler.add_job(
            check_unusual_spending,
            CronTrigger(hour='*/6'),
            id='unusual_spending',
            name='Check unusual spending',
            replace_existing=True
        )
        
        # Run immediately on startup (for testing)
        scheduler.add_job(
            process_due_recurring_payments,
            'date',
            run_date=datetime.now(),
            id='process_recurring_startup'
        )
        
        scheduler.start()
        logger.info("Scheduler started successfully")
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")

def stop_scheduler():
    """Stop the background scheduler"""
    try:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
