"""
Transaction management routes
"""
from flask import Blueprint, request, jsonify
from database import Database
from auth import require_auth
from datetime import datetime

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

@transactions_bp.route('/', methods=['GET'])
@require_auth
def get_transactions():
    """Get all transactions for current user with optional filters"""
    try:
        # Get query parameters
        account_id = request.args.get('account_id', type=int)
        category_id = request.args.get('category_id', type=int)
        group_id = request.args.get('group_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = """
            SELECT 
                t.transaction_id, t.amount, t.original_amount, t.currency_code,
                t.exchange_rate, t.transaction_date, t.description,
                t.account_id, a.account_name, a.account_type,
                t.category_id, c.category_name, c.type as category_type,
                t.group_id, t.recurring_id
            FROM Transactions t
            JOIN Accounts a ON t.account_id = a.account_id
            JOIN Categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s
        """
        params = [request.user_id]
        
        if account_id:
            query += " AND t.account_id = %s"
            params.append(account_id)
        
        if category_id:
            query += " AND t.category_id = %s"
            params.append(category_id)
        
        if group_id:
            query += " AND t.group_id = %s"
            params.append(group_id)
        
        if start_date:
            query += " AND t.transaction_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND t.transaction_date <= %s"
            params.append(end_date)
        
        query += " ORDER BY t.transaction_date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        transactions = Database.execute_query(query, tuple(params), fetch_all=True)
        # Ensure transaction_date stays in local datetime string format (YYYY-MM-DD HH:mm:ss)
        for t in transactions:
            if t.get('transaction_date') is not None:
                try:
                    t['transaction_date'] = t['transaction_date'].strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    # If already a string, leave as-is
                    pass
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as total
            FROM Transactions t
            WHERE t.user_id = %s
        """
        count_params = [request.user_id]
        
        if account_id:
            count_query += " AND t.account_id = %s"
            count_params.append(account_id)
        
        if category_id:
            count_query += " AND t.category_id = %s"
            count_params.append(category_id)
        
        if group_id:
            count_query += " AND t.group_id = %s"
            count_params.append(group_id)
        
        if start_date:
            count_query += " AND t.transaction_date >= %s"
            count_params.append(start_date)
        
        if end_date:
            count_query += " AND t.transaction_date <= %s"
            count_params.append(end_date)
        
        total = Database.execute_query(count_query, tuple(count_params), fetch_one=True)
        
        return jsonify({
            'transactions': transactions,
            'total': total['total'],
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transactions_bp.route('/<int:transaction_id>', methods=['GET'])
@require_auth
def get_transaction(transaction_id):
    """Get specific transaction"""
    try:
        transaction = Database.execute_query(
            """
            SELECT 
                t.transaction_id, t.amount, t.original_amount, t.currency_code,
                t.exchange_rate, t.transaction_date, t.description,
                t.account_id, a.account_name, a.account_type,
                t.category_id, c.category_name, c.type as category_type,
                t.group_id, t.recurring_id
            FROM Transactions t
            JOIN Accounts a ON t.account_id = a.account_id
            JOIN Categories c ON t.category_id = c.category_id
            WHERE t.transaction_id = %s AND t.user_id = %s
            """,
            (transaction_id, request.user_id),
            fetch_one=True
        )
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        # Format transaction_date to local string
        if transaction.get('transaction_date') is not None:
            try:
                transaction['transaction_date'] = transaction['transaction_date'].strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                pass

        return jsonify({'transaction': transaction}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transactions_bp.route('/', methods=['POST'])
@require_auth
def create_transaction():
    """Create new transaction"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['account_id', 'category_id', 'amount', 'transaction_date']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Verify account belongs to user
        account = Database.execute_query(
            "SELECT account_id FROM Accounts WHERE account_id = %s AND user_id = %s",
            (data['account_id'], request.user_id),
            fetch_one=True
        )
        
        if not account:
            return jsonify({'error': 'Invalid account'}), 400
        
        # Insert transaction
        transaction_id = Database.execute_query(
            """
            INSERT INTO Transactions 
            (user_id, account_id, category_id, group_id, recurring_id, amount, 
             original_amount, currency_code, exchange_rate, transaction_date, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                request.user_id,
                data['account_id'],
                data['category_id'],
                data.get('group_id'),
                data.get('recurring_id'),
                data['amount'],
                data.get('original_amount'),
                data.get('currency_code', 'VND'),
                data.get('exchange_rate', 1.0),
                data['transaction_date'],
                data.get('description', '')
            ),
            commit=True
        )
        
        # Check for unusual spending alert
        alert = check_unusual_spending(request.user_id, data['category_id'], data['amount'])
        
        response = {
            'message': 'Transaction created successfully',
            'transaction_id': transaction_id
        }
        
        if alert:
            response['alert'] = alert
        
        return jsonify(response), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transactions_bp.route('/<int:transaction_id>', methods=['PUT'])
@require_auth
def update_transaction(transaction_id):
    """Update transaction"""
    try:
        data = request.get_json()
        
        # Check if transaction belongs to user
        transaction = Database.execute_query(
            "SELECT transaction_id FROM Transactions WHERE transaction_id = %s AND user_id = %s",
            (transaction_id, request.user_id),
            fetch_one=True
        )
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        # Build update query
        update_fields = []
        params = []
        
        allowed_fields = ['account_id', 'category_id', 'amount', 'original_amount', 
                         'currency_code', 'exchange_rate', 'transaction_date', 'description']
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        params.extend([transaction_id, request.user_id])
        
        Database.execute_query(
            f"UPDATE Transactions SET {', '.join(update_fields)} WHERE transaction_id = %s AND user_id = %s",
            tuple(params),
            commit=True
        )
        
        return jsonify({'message': 'Transaction updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transactions_bp.route('/<int:transaction_id>', methods=['DELETE'])
@require_auth
def delete_transaction(transaction_id):
    """Delete transaction"""
    try:
        # Check if transaction belongs to user
        transaction = Database.execute_query(
            "SELECT transaction_id FROM Transactions WHERE transaction_id = %s AND user_id = %s",
            (transaction_id, request.user_id),
            fetch_one=True
        )
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        Database.execute_query(
            "DELETE FROM Transactions WHERE transaction_id = %s AND user_id = %s",
            (transaction_id, request.user_id),
            commit=True
        )
        
        return jsonify({'message': 'Transaction deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_unusual_spending(user_id, category_id, amount):
    """Check if transaction amount is unusual compared to historical average"""
    try:
        stats = Database.execute_query(
            """
            SELECT average_spent, max_spent
            FROM View_Category_Alert_Stats
            WHERE user_id = %s AND category_id = %s
            """,
            (user_id, category_id),
            fetch_one=True
        )
        
        if stats and stats['average_spent']:
            avg = float(stats['average_spent'])
            threshold = avg * 1.25  # 25% above average
            
            if amount > threshold:
                return {
                    'unusual': True,
                    'message': f'This transaction is {((amount - avg) / avg * 100):.1f}% higher than your average',
                    'average': avg,
                    'current': amount
                }
        
        return None
        
    except Exception as e:
        print(f"Alert check error: {e}")
        return None
