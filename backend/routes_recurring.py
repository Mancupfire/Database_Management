"""
Recurring payments management routes
"""
from flask import Blueprint, request, jsonify
from database import Database
from auth import require_auth
from datetime import datetime, timedelta

recurring_bp = Blueprint('recurring', __name__, url_prefix='/api/recurring')

@recurring_bp.route('/', methods=['GET'])
@require_auth
def get_recurring_payments():
    """Get all recurring payments for current user"""
    try:
        # Get sorting parameters
        sort_by = request.args.get('sort_by', 'next_due_date')  # date, amount
        sort_order = request.args.get('sort_order', 'asc')  # asc, desc
        
        # Validate sort parameters
        valid_sort_by = {'next_due_date': 'r.next_due_date', 'amount': 'r.amount'}
        valid_sort_order = {'asc': 'ASC', 'desc': 'DESC'}
        
        order_column = valid_sort_by.get(sort_by, 'r.next_due_date')
        order_direction = valid_sort_order.get(sort_order, 'ASC')
        
        query = f"""
            SELECT 
                r.recurring_id, r.amount, r.frequency,
                r.start_date, r.next_due_date, r.is_active,
                r.account_id, a.account_name,
                r.category_id, c.category_name,
                DATEDIFF(r.next_due_date, DATE(NOW())) as days_until_due
            FROM Recurring_Payments r
            JOIN Accounts a ON r.account_id = a.account_id
            JOIN Categories c ON r.category_id = c.category_id
            WHERE r.user_id = %s
            ORDER BY {order_column} {order_direction}, r.is_active DESC
        """
        
        payments = Database.execute_query(query, (request.user_id,), fetch_all=True)
        
        for payment in payments:
            payment['amount'] = float(payment['amount'])
            payment['start_date'] = payment['start_date'].strftime('%Y-%m-%d')
            payment['next_due_date'] = payment['next_due_date'].strftime('%Y-%m-%d')
            payment['is_active'] = bool(payment['is_active'])
            payment['is_overdue'] = payment['days_until_due'] < 0
            payment['is_due_soon'] = 0 <= payment['days_until_due'] <= 7
        
        return jsonify(payments), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recurring_bp.route('/<int:recurring_id>', methods=['GET'])
@require_auth
def get_recurring_payment(recurring_id):
    """Get details of a specific recurring payment"""
    try:
        query = """
            SELECT 
                r.recurring_id, r.amount, r.frequency,
                r.start_date, r.next_due_date, r.is_active,
                r.account_id, a.account_name,
                r.category_id, c.category_name
            FROM Recurring_Payments r
            JOIN Accounts a ON r.account_id = a.account_id
            JOIN Categories c ON r.category_id = c.category_id
            WHERE r.recurring_id = %s AND r.user_id = %s
        """
        
        payment = Database.execute_query(
            query, (recurring_id, request.user_id), fetch_one=True
        )
        
        if not payment:
            return jsonify({'error': 'Recurring payment not found'}), 404
        
        payment['amount'] = float(payment['amount'])
        payment['start_date'] = payment['start_date'].strftime('%Y-%m-%d')
        payment['next_due_date'] = payment['next_due_date'].strftime('%Y-%m-%d')
        payment['is_active'] = bool(payment['is_active'])
        
        return jsonify(payment), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recurring_bp.route('/', methods=['POST'])
@require_auth
def create_recurring_payment():
    """Create a new recurring payment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['account_id', 'category_id', 'amount', 'frequency', 'start_date']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate frequency
        valid_frequencies = ['Daily', 'Weekly', 'Monthly', 'Yearly']
        if data['frequency'] not in valid_frequencies:
            return jsonify({'error': f'Frequency must be one of: {valid_frequencies}'}), 400
        
        # Validate account belongs to user
        account_check = """
            SELECT account_id FROM Accounts 
            WHERE account_id = %s AND user_id = %s
        """
        account = Database.execute_query(
            account_check, (data['account_id'], request.user_id), fetch_one=True
        )
        
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        # Parse start date
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Calculate next due date
        next_due_date = start_date
        
        # Insert recurring payment
        query = """
            INSERT INTO Recurring_Payments 
            (user_id, account_id, category_id, amount, frequency, start_date, next_due_date, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
        """
        
        recurring_id = Database.execute_query(
            query,
            (request.user_id, data['account_id'], data['category_id'],
             data['amount'], data['frequency'], start_date, next_due_date),
            commit=True
        )
        
        return jsonify({
            'message': 'Recurring payment created successfully',
            'recurring_id': recurring_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recurring_bp.route('/<int:recurring_id>', methods=['PUT'])
@require_auth
def update_recurring_payment(recurring_id):
    """Update a recurring payment"""
    try:
        data = request.get_json()
        
        # Verify payment belongs to user
        check_query = """
            SELECT recurring_id FROM Recurring_Payments 
            WHERE recurring_id = %s AND user_id = %s
        """
        payment = Database.execute_query(
            check_query, (recurring_id, request.user_id), fetch_one=True
        )
        
        if not payment:
            return jsonify({'error': 'Recurring payment not found'}), 404
        
        # Build update query dynamically
        updates = []
        params = []
        
        if 'amount' in data:
            updates.append("amount = %s")
            params.append(data['amount'])
        
        if 'frequency' in data:
            valid_frequencies = ['Daily', 'Weekly', 'Monthly', 'Yearly']
            if data['frequency'] not in valid_frequencies:
                return jsonify({'error': f'Frequency must be one of: {valid_frequencies}'}), 400
            updates.append("frequency = %s")
            params.append(data['frequency'])
        
        if 'account_id' in data:
            # Validate account belongs to user
            account_check = Database.execute_query(
                "SELECT account_id FROM Accounts WHERE account_id = %s AND user_id = %s",
                (data['account_id'], request.user_id),
                fetch_one=True
            )
            if not account_check:
                return jsonify({'error': 'Account not found'}), 404
            updates.append("account_id = %s")
            params.append(data['account_id'])
        
        if 'category_id' in data:
            updates.append("category_id = %s")
            params.append(data['category_id'])
        
        if 'start_date' in data:
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                updates.append("start_date = %s")
                params.append(start_date)
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if 'is_active' in data:
            updates.append("is_active = %s")
            params.append(data['is_active'])
        
        if not updates:
            return jsonify({'error': 'No fields to update'}), 400
        
        params.append(recurring_id)
        query = f"UPDATE Recurring_Payments SET {', '.join(updates)} WHERE recurring_id = %s"
        
        Database.execute_query(query, tuple(params), commit=True)
        
        return jsonify({'message': 'Recurring payment updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recurring_bp.route('/<int:recurring_id>', methods=['DELETE'])
@require_auth
def delete_recurring_payment(recurring_id):
    """Delete a recurring payment"""
    try:
        # Verify payment belongs to user
        check_query = """
            SELECT recurring_id FROM Recurring_Payments 
            WHERE recurring_id = %s AND user_id = %s
        """
        payment = Database.execute_query(
            check_query, (recurring_id, request.user_id), fetch_one=True
        )
        
        if not payment:
            return jsonify({'error': 'Recurring payment not found'}), 404
        
        query = "DELETE FROM Recurring_Payments WHERE recurring_id = %s"
        Database.execute_query(query, (recurring_id,), commit=True)
        
        return jsonify({'message': 'Recurring payment deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recurring_bp.route('/<int:recurring_id>/execute', methods=['POST'])
@require_auth
def execute_recurring_payment(recurring_id):
    """Execute a recurring payment (create transaction and update next due date)"""
    try:
        # Verify payment belongs to user and is active
        check_query = """
            SELECT recurring_id, is_active 
            FROM Recurring_Payments 
            WHERE recurring_id = %s AND user_id = %s
        """
        payment = Database.execute_query(
            check_query, (recurring_id, request.user_id), fetch_one=True
        )
        
        if not payment:
            return jsonify({'error': 'Recurring payment not found'}), 404
        
        if not payment['is_active']:
            return jsonify({'error': 'Recurring payment is not active'}), 400
        
        # Get transaction datetime from request body (GMT+7 time from frontend)
        data = request.get_json() or {}
        transaction_datetime = data.get('transaction_datetime')
        
        # Call stored procedure with datetime parameter
        query = "CALL SP_Create_Recurring_Transaction(%s, %s)"
        Database.execute_query(query, (recurring_id, transaction_datetime), commit=True)
        
        return jsonify({
            'message': 'Recurring payment executed successfully',
            'transaction_created': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recurring_bp.route('/due', methods=['GET'])
@require_auth
def get_due_payments():
    """Get all due or overdue recurring payments"""
    try:
        query = """
            SELECT 
                r.recurring_id, r.amount, r.frequency,
                r.next_due_date, r.account_id, a.account_name,
                r.category_id, c.category_name,
                DATEDIFF(CURDATE(), r.next_due_date) as days_overdue
            FROM Recurring_Payments r
            JOIN Accounts a ON r.account_id = a.account_id
            JOIN Categories c ON r.category_id = c.category_id
            WHERE r.user_id = %s 
            AND r.is_active = TRUE
            AND r.next_due_date <= CURDATE()
            ORDER BY r.next_due_date
        """
        
        payments = Database.execute_query(query, (request.user_id,), fetch_all=True)
        
        for payment in payments:
            payment['amount'] = float(payment['amount'])
            payment['next_due_date'] = payment['next_due_date'].strftime('%Y-%m-%d')
        
        return jsonify(payments), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@recurring_bp.route('/upcoming', methods=['GET'])
@require_auth
def get_upcoming_payments():
    """Get upcoming recurring payments using View_Upcoming_Recurring_Payments"""
    try:
        query = """
            SELECT 
                recurring_id, amount, frequency, next_due_date,
                account_id, account_name, category_id, category_name,
                description, days_until_due, due_status, urgency_level
            FROM View_Upcoming_Recurring_Payments
            WHERE user_id = %s
            ORDER BY next_due_date ASC
        """
        
        payments = Database.execute_query(query, (request.user_id,), fetch_all=True)
        
        for payment in payments:
            payment['amount'] = float(payment['amount'])
            payment['next_due_date'] = payment['next_due_date'].strftime('%Y-%m-%d')
        
        return jsonify(payments), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500