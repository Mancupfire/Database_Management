"""
Analytics and Reporting routes
"""
from flask import Blueprint, request, jsonify
from database import Database
from auth import require_auth

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/dashboard', methods=['GET'])
@require_auth
def get_dashboard():
    """Get dashboard overview"""
    try:
        # Get account summary
        accounts = Database.execute_query(
            """
            SELECT 
                COUNT(*) as total_accounts,
                COALESCE(SUM(balance), 0) as total_balance
            FROM Accounts
            WHERE user_id = %s
            """,
            (request.user_id,),
            fetch_one=True
        )
        
        # Get monthly income/expense
        monthly = Database.execute_query(
            """
            SELECT 
                c.type,
                COALESCE(SUM(t.amount), 0) as total
            FROM Transactions t
            JOIN Categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s 
            AND t.transaction_date >= DATE_FORMAT(NOW(), '%Y-%m-01')
            GROUP BY c.type
            """,
            (request.user_id,),
            fetch_all=True
        )
        
        monthly_data = {row['type']: float(row['total']) for row in monthly}
        
        # Get recent transactions
        recent = Database.execute_query(
            """
            SELECT 
                t.transaction_id, t.amount, t.transaction_date, t.description,
                a.account_name, c.category_name, c.type as category_type
            FROM Transactions t
            JOIN Accounts a ON t.account_id = a.account_id
            JOIN Categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s
            ORDER BY t.transaction_date DESC
            LIMIT 10
            """,
            (request.user_id,),
            fetch_all=True
        )
        
        return jsonify({
            'accounts': {
                'total': accounts['total_accounts'],
                'balance': float(accounts['total_balance'] or 0)
            },
            'current_month': {
                'income': monthly_data.get('Income', 0),
                'expense': monthly_data.get('Expense', 0),
                'net': monthly_data.get('Income', 0) - monthly_data.get('Expense', 0)
            },
            'recent_transactions': recent
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/monthly-report', methods=['GET'])
@require_auth
def get_monthly_report():
    """Get monthly report from view"""
    try:
        # Get month parameter (default to current month)
        month_year = request.args.get('month', None)
        
        query = """
            SELECT month_year, category_name, type, total_amount
            FROM View_Monthly_Report
            WHERE user_id = %s
        """
        params = [request.user_id]
        
        if month_year:
            query += " AND month_year = %s"
            params.append(month_year)
        
        query += " ORDER BY month_year DESC, type, category_name"
        
        report = Database.execute_query(query, tuple(params), fetch_all=True)
        
        return jsonify({'report': report}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/spending-by-category', methods=['GET'])
@require_auth
def get_spending_by_category():
    """Get spending breakdown by category"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = """
            SELECT 
                c.category_name,
                c.type,
                COUNT(t.transaction_id) as transaction_count,
                SUM(t.amount) as total_amount,
                AVG(t.amount) as avg_amount,
                MIN(t.amount) as min_amount,
                MAX(t.amount) as max_amount
            FROM Transactions t
            JOIN Categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s
        """
        params = [request.user_id]
        
        if start_date:
            query += " AND t.transaction_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND t.transaction_date <= %s"
            params.append(end_date)
        
        query += " GROUP BY c.category_id, c.category_name, c.type ORDER BY total_amount DESC"
        
        data = Database.execute_query(query, tuple(params), fetch_all=True)
        
        return jsonify({'categories': data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/trends', methods=['GET'])
@require_auth
def get_trends():
    """Get spending trends over time"""
    try:
        months = request.args.get('months', 6, type=int)
        
        trends = Database.execute_query(
            """
            SELECT 
                DATE_FORMAT(t.transaction_date, '%Y-%m') as month,
                c.type,
                SUM(t.amount) as total
            FROM Transactions t
            JOIN Categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s
            AND t.transaction_date >= DATE_SUB(NOW(), INTERVAL %s MONTH)
            GROUP BY month, c.type
            ORDER BY month DESC, c.type
            """,
            (request.user_id, months),
            fetch_all=True
        )
        
        return jsonify({'trends': trends}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/monthly-trends', methods=['GET'])
@require_auth
def get_monthly_trends():
    """Get window-function based monthly trends (running totals + rolling averages)"""
    try:
        months = request.args.get('months', 12, type=int)
        txn_type = request.args.get('type')

        query = """
            SELECT 
                month_year,
                type,
                monthly_total,
                running_total,
                rolling_avg_3m
            FROM View_Monthly_Trends_Window
            WHERE user_id = %s
        """
        params = [request.user_id]

        if txn_type:
            query += " AND type = %s"
            params.append(txn_type)

        if months:
            query += " AND month_year >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL %s MONTH), '%Y-%m')"
            params.append(months)

        query += " ORDER BY month_year DESC, type"

        trends = Database.execute_query(query, tuple(params), fetch_all=True)

        return jsonify({'monthly_trends': trends}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/budget-status', methods=['GET'])
@require_auth
def get_budget_status():
    """Get budget status for current month"""
    try:
        budgets = Database.execute_query(
            """
            SELECT 
                b.budget_id,
                b.category_id,
                c.category_name,
                b.amount_limit,
                b.start_date,
                b.end_date,
                COALESCE(SUM(t.amount), 0) as spent
            FROM Budgets b
            JOIN Categories c ON b.category_id = c.category_id
            LEFT JOIN Transactions t ON t.category_id = b.category_id 
                AND t.user_id = b.user_id
                AND t.transaction_date BETWEEN b.start_date AND b.end_date
            WHERE b.user_id = %s
            AND b.start_date <= CURDATE()
            AND b.end_date >= CURDATE()
            GROUP BY b.budget_id, b.category_id, c.category_name, b.amount_limit, b.start_date, b.end_date
            """,
            (request.user_id,),
            fetch_all=True
        )
        
        # Calculate percentage and status for each budget
        for budget in budgets:
            spent = float(budget['spent'])
            limit = float(budget['amount_limit'])
            percentage = (spent / limit * 100) if limit > 0 else 0
            
            budget['spent'] = spent
            budget['amount_limit'] = limit
            budget['percentage'] = round(percentage, 2)
            budget['remaining'] = limit - spent
            
            if percentage >= 100:
                budget['status'] = 'EXCEEDED'
            elif percentage >= 80:
                budget['status'] = 'WARNING'
            elif percentage >= 50:
                budget['status'] = 'NORMAL'
            else:
                budget['status'] = 'SAFE'
        
        return jsonify({'budgets': budgets}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/unusual-spending', methods=['GET'])
@require_auth
def get_unusual_spending():
    """Get unusual spending alerts"""
    try:
        alerts = Database.execute_query(
            """
            SELECT 
                v.category_id,
                c.category_name,
                v.average_spent,
                v.max_spent,
                (v.average_spent * 1.25) as alert_threshold
            FROM View_Category_Alert_Stats v
            JOIN Categories c ON v.category_id = c.category_id
            WHERE v.user_id = %s
            ORDER BY v.average_spent DESC
            """,
            (request.user_id,),
            fetch_all=True
        )
        
        return jsonify({'alerts': alerts}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
