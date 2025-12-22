"""
Budget management routes
"""
from flask import Blueprint, request, jsonify
from database import Database
from auth import require_auth
from datetime import datetime

budgets_bp = Blueprint('budgets', __name__, url_prefix='/api/budgets')

@budgets_bp.route('/', methods=['GET'])
@require_auth
def get_budgets():
    """Get all budgets for current user"""
    try:
        query = """
            SELECT 
                b.budget_id, b.category_id, c.category_name,
                b.amount_limit, b.start_date, b.end_date,
                b.created_at,
                COALESCE(SUM(t.amount), 0) as spent
            FROM Budgets b
            JOIN Categories c ON b.category_id = c.category_id
            LEFT JOIN Transactions t ON 
                t.user_id = b.user_id AND 
                t.category_id = b.category_id AND
                t.transaction_date BETWEEN b.start_date AND b.end_date AND
                c.type = 'Expense'
            WHERE b.user_id = %s
            GROUP BY b.budget_id, b.category_id, c.category_name, 
                     b.amount_limit, b.start_date, b.end_date, b.created_at
            ORDER BY b.start_date DESC
        """
        
        budgets = Database.execute_query(query, (request.user_id,), fetch_all=True)
        
        # Calculate percentage and status for each budget
        for budget in budgets:
            budget['spent'] = float(budget['spent'])
            budget['amount_limit'] = float(budget['amount_limit'])
            
            if budget['amount_limit'] > 0:
                budget['percentage'] = round((budget['spent'] / budget['amount_limit']) * 100, 2)
            else:
                budget['percentage'] = 0
            
            # Status based on percentage
            if budget['percentage'] >= 100:
                budget['status'] = 'EXCEEDED'
            elif budget['percentage'] >= 80:
                budget['status'] = 'WARNING'
            elif budget['percentage'] >= 50:
                budget['status'] = 'NORMAL'
            else:
                budget['status'] = 'SAFE'
            
            # Convert dates to strings
            budget['start_date'] = budget['start_date'].strftime('%Y-%m-%d')
            budget['end_date'] = budget['end_date'].strftime('%Y-%m-%d')
            budget['created_at'] = budget['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify(budgets), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@budgets_bp.route('/<int:budget_id>', methods=['GET'])
@require_auth
def get_budget(budget_id):
    """Get a single budget by ID"""
    try:
        query = """
            SELECT 
                b.budget_id, b.category_id, c.category_name,
                b.amount_limit, b.start_date, b.end_date,
                b.created_at
            FROM Budgets b
            JOIN Categories c ON b.category_id = c.category_id
            WHERE b.budget_id = %s AND b.user_id = %s
        """
        
        budget = Database.execute_query(query, (budget_id, request.user_id), fetch_one=True)
        
        if not budget:
            return jsonify({'error': 'Budget not found'}), 404
        
        # Convert dates to strings
        budget['start_date'] = budget['start_date'].strftime('%Y-%m-%d')
        budget['end_date'] = budget['end_date'].strftime('%Y-%m-%d')
        budget['created_at'] = budget['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        budget['amount_limit'] = float(budget['amount_limit'])
        
        return jsonify(budget), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@budgets_bp.route('/', methods=['POST'])
@require_auth
def create_budget():
    """Create a new budget"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['category_id', 'amount_limit', 'start_date', 'end_date']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if end_date <= start_date:
            return jsonify({'error': 'End date must be after start date'}), 400
        
        # Check if budget already exists for this category and period
        check_query = """
            SELECT budget_id FROM Budgets 
            WHERE user_id = %s AND category_id = %s
            AND (
                (start_date <= %s AND end_date >= %s) OR
                (start_date <= %s AND end_date >= %s) OR
                (start_date >= %s AND end_date <= %s)
            )
        """
        existing = Database.execute_query(
            check_query, 
            (request.user_id, data['category_id'], 
             start_date, start_date, end_date, end_date,
             start_date, end_date),
            fetch_one=True
        )
        
        if existing:
            return jsonify({'error': 'Budget already exists for this category in overlapping period'}), 409
        
        # Insert budget
        query = """
            INSERT INTO Budgets (user_id, category_id, amount_limit, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        budget_id = Database.execute_query(
            query,
            (request.user_id, data['category_id'], data['amount_limit'], 
             start_date, end_date),
            commit=True
        )
        
        return jsonify({
            'message': 'Budget created successfully',
            'budget_id': budget_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@budgets_bp.route('/<int:budget_id>', methods=['PUT'])
@require_auth
def update_budget(budget_id):
    """Update a budget"""
    try:
        data = request.get_json()
        
        # Verify budget belongs to user
        check_query = "SELECT budget_id FROM Budgets WHERE budget_id = %s AND user_id = %s"
        budget = Database.execute_query(check_query, (budget_id, request.user_id), fetch_one=True)
        
        if not budget:
            return jsonify({'error': 'Budget not found'}), 404
        
        # Build update query dynamically
        updates = []
        params = []
        
        if 'amount_limit' in data:
            updates.append("amount_limit = %s")
            params.append(data['amount_limit'])
        
        if 'start_date' in data:
            updates.append("start_date = %s")
            params.append(data['start_date'])
        
        if 'end_date' in data:
            updates.append("end_date = %s")
            params.append(data['end_date'])
        
        if not updates:
            return jsonify({'error': 'No fields to update'}), 400
        
        params.append(budget_id)
        query = f"UPDATE Budgets SET {', '.join(updates)} WHERE budget_id = %s"
        
        Database.execute_query(query, tuple(params), commit=True)
        
        return jsonify({'message': 'Budget updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@budgets_bp.route('/<int:budget_id>', methods=['DELETE'])
@require_auth
def delete_budget(budget_id):
    """Delete a budget"""
    try:
        # Verify budget belongs to user
        check_query = "SELECT budget_id FROM Budgets WHERE budget_id = %s AND user_id = %s"
        budget = Database.execute_query(check_query, (budget_id, request.user_id), fetch_one=True)
        
        if not budget:
            return jsonify({'error': 'Budget not found'}), 404
        
        query = "DELETE FROM Budgets WHERE budget_id = %s"
        Database.execute_query(query, (budget_id,), commit=True)
        
        return jsonify({'message': 'Budget deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@budgets_bp.route('/check/<int:category_id>', methods=['GET'])
@require_auth
def check_budget_status(category_id):
    """Check budget status for a category in current month"""
    try:
        # Call stored procedure
        query = """
            SET @limit = 0, @spent = 0, @percentage = 0, @status = '';
            CALL SP_Check_Budget_Alert(%s, %s, 
                DATE_FORMAT(NOW(), '%%Y-%%m-01'),
                LAST_DAY(NOW()),
                @limit, @spent, @percentage, @status);
            SELECT @limit as budget_limit, @spent as total_spent, 
                   @percentage as percentage_used, @status as alert_status;
        """
        
        result = Database.execute_query(
            query,
            (request.user_id, category_id),
            fetch_one=True
        )
        
        if not result or result['budget_limit'] is None:
            return jsonify({
                'message': 'No budget set for this category',
                'has_budget': False
            }), 200
        
        return jsonify({
            'has_budget': True,
            'budget_limit': float(result['budget_limit']),
            'total_spent': float(result['total_spent']),
            'percentage_used': float(result['percentage_used']),
            'alert_status': result['alert_status']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
