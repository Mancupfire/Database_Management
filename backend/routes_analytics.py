"""
Analytics and Reporting routes
"""
from flask import Blueprint, request, jsonify
from database import Database
from auth import require_auth
from datetime import datetime

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
            AND t.transaction_date >= DATE_FORMAT(NOW(), '%%Y-%%m-01')
            GROUP BY c.type
            """,
            (request.user_id,),
            fetch_all=True
        )
        
        monthly_data = {}
        if monthly:
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
        import traceback
        print(f"Dashboard error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'accounts': {'total': 0, 'balance': 0},
            'current_month': {'income': 0, 'expense': 0, 'net': 0},
            'recent_transactions': []
        }), 200  # Return 200 with empty data instead of 500
        print(traceback.format_exc())
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

@analytics_bp.route('/monthly-trend', methods=['GET'])
@require_auth
def get_monthly_trend():
    """Get income/expense trend for last 6 months"""
    try:
        # Get parameter for number of months (default 6, max 12)
        months = min(int(request.args.get('months', 6)), 12)
        
        trend_data = Database.execute_query(
            """
            SELECT 
                DATE_FORMAT(t.transaction_date, '%%Y-%%m') as month,
                c.type,
                SUM(ABS(t.amount)) as total
            FROM Transactions t
            JOIN Categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s
            AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
            GROUP BY DATE_FORMAT(t.transaction_date, '%%Y-%%m'), c.type
            ORDER BY month ASC
            """,
            (request.user_id, months),
            fetch_all=True
        )
        
        # Format data for Chart.js
        months_list = []
        income_data = []
        expense_data = []
        
        # Group by month
        month_map = {}
        for row in trend_data:
            month = row['month']
            if month not in month_map:
                month_map[month] = {'Income': 0, 'Expense': 0}
            month_map[month][row['type']] = float(row['total'])
        
        # Sort and prepare arrays
        for month in sorted(month_map.keys()):
            months_list.append(month)
            income_data.append(month_map[month]['Income'])
            expense_data.append(month_map[month]['Expense'])
        
        return jsonify({
            'labels': months_list,
            'datasets': [
                {
                    'label': 'Income',
                    'data': income_data,
                    'backgroundColor': 'rgba(75, 192, 192, 0.6)',
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'borderWidth': 2
                },
                {
                    'label': 'Expense',
                    'data': expense_data,
                    'backgroundColor': 'rgba(255, 99, 132, 0.6)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'borderWidth': 2
                }
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/yearly-summary', methods=['GET'])
@require_auth
def get_yearly_summary():
    """Get yearly income/expense summary"""
    try:
        year = request.args.get('year', datetime.now().year)
        
        yearly_data = Database.execute_query(
            """
            SELECT 
                MONTH(t.transaction_date) as month,
                c.type,
                SUM(ABS(t.amount)) as total
            FROM Transactions t
            JOIN Categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s
            AND YEAR(t.transaction_date) = %s
            GROUP BY MONTH(t.transaction_date), c.type
            ORDER BY month ASC
            """,
            (request.user_id, year),
            fetch_all=True
        )
        
        # Prepare data for all 12 months
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        income_data = [0] * 12
        expense_data = [0] * 12
        
        for row in yearly_data:
            month_idx = row['month'] - 1
            if row['type'] == 'Income':
                income_data[month_idx] = float(row['total'])
            else:
                expense_data[month_idx] = float(row['total'])
        
        return jsonify({
            'year': year,
            'labels': month_names,
            'datasets': [
                {
                    'label': 'Income',
                    'data': income_data,
                    'backgroundColor': 'rgba(75, 192, 192, 0.6)',
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'borderWidth': 2
                },
                {
                    'label': 'Expense',
                    'data': expense_data,
                    'backgroundColor': 'rgba(255, 99, 132, 0.6)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'borderWidth': 2
                }
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
