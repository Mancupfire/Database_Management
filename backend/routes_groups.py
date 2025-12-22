"""
Group management routes for shared expenses
"""
from flask import Blueprint, request, jsonify
from database import Database
from auth import require_auth
from datetime import datetime

groups_bp = Blueprint('groups', __name__, url_prefix='/api/groups')

@groups_bp.route('/', methods=['GET'])
@require_auth
def get_groups():
    """Get all groups for current user"""
    try:
        query = """
            SELECT 
                g.group_id, g.group_name, g.created_at,
                g.created_by, u.username as creator_name,
                COUNT(DISTINCT ug.user_id) as member_count,
                COALESCE(SUM(CASE WHEN c.type = 'Expense' THEN ABS(t.amount) ELSE 0 END), 0) as total_spent
            FROM `Groups` g
            JOIN User_Groups ug ON g.group_id = ug.group_id
            LEFT JOIN Users u ON g.created_by = u.user_id
            LEFT JOIN Transactions t ON g.group_id = t.group_id
            LEFT JOIN Categories c ON t.category_id = c.category_id
            WHERE ug.user_id = %s
            GROUP BY g.group_id, g.group_name, g.created_at, g.created_by, u.username
            ORDER BY g.created_at DESC
        """
        
        groups = Database.execute_query(query, (request.user_id,), fetch_all=True)
        
        for group in groups:
            group['total_spent'] = float(group['total_spent'])
            group['created_at'] = group['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            group['is_creator'] = group['created_by'] == request.user_id
        
        return jsonify(groups), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>', methods=['GET'])
@require_auth
def get_group_details(group_id):
    """Get detailed information about a group"""
    try:
        # Verify user is member
        member_check = """
            SELECT user_id FROM User_Groups 
            WHERE group_id = %s AND user_id = %s
        """
        is_member = Database.execute_query(
            member_check, (group_id, request.user_id), fetch_one=True
        )
        
        if not is_member:
            return jsonify({'error': 'You are not a member of this group'}), 403
        
        # Get group info with total spending (only expenses assigned to this group)
        group_query = """
            SELECT g.group_id, g.group_name, g.created_at,
                   g.created_by, creator.username as creator_name,
                   COALESCE(SUM(CASE WHEN c.type = 'Expense' THEN ABS(t.amount) ELSE 0 END), 0) as total_spent
            FROM `Groups` g
            LEFT JOIN Users creator ON g.created_by = creator.user_id
            LEFT JOIN Transactions t ON g.group_id = t.group_id
            LEFT JOIN Categories c ON t.category_id = c.category_id
            WHERE g.group_id = %s
            GROUP BY g.group_id, g.group_name, g.created_at, g.created_by, creator.username
        """
        group = Database.execute_query(group_query, (group_id,), fetch_one=True)
        
        if not group:
            return jsonify({'error': 'Group not found'}), 404
        
        # Get members
        members_query = """
            SELECT u.user_id, u.username, u.email, ug.joined_at
            FROM User_Groups ug
            JOIN Users u ON ug.user_id = u.user_id
            WHERE ug.group_id = %s
            ORDER BY ug.joined_at
        """
        members = Database.execute_query(members_query, (group_id,), fetch_all=True)
        
        # Get recent transactions
        transactions_query = """
            SELECT 
                t.transaction_id, t.amount, t.transaction_date, 
                t.description, u.username,
                c.category_name, a.account_name
            FROM Transactions t
            JOIN Users u ON t.user_id = u.user_id
            JOIN Categories c ON t.category_id = c.category_id
            JOIN Accounts a ON t.account_id = a.account_id
            WHERE t.group_id = %s
            ORDER BY t.transaction_date DESC
            LIMIT 20
        """
        transactions = Database.execute_query(transactions_query, (group_id,), fetch_all=True)
        
        # Format dates and numbers
        group['created_at'] = group['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        group['is_creator'] = group['created_by'] == request.user_id
        group['total_spent'] = float(group['total_spent']) if group['total_spent'] else 0.0
        group['members'] = members  # Add members to group object for easy access
        
        for member in members:
            member['joined_at'] = member['joined_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        for tx in transactions:
            tx['amount'] = float(tx['amount'])
            tx['transaction_date'] = tx['transaction_date'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'group': group,
            'members': members,
            'recent_transactions': transactions
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/', methods=['POST'])
@require_auth
def create_group():
    """Create a new group"""
    try:
        data = request.get_json()
        
        if 'group_name' not in data:
            return jsonify({'error': 'Group name is required'}), 400
        
        # Create group
        insert_query = """
            INSERT INTO `Groups` (group_name, created_by)
            VALUES (%s, %s)
        """
        group_id = Database.execute_query(
            insert_query,
            (data['group_name'], request.user_id),
            commit=True
        )
        
        # Add creator as member
        member_query = """
            INSERT INTO User_Groups (user_id, group_id)
            VALUES (%s, %s)
        """
        Database.execute_query(member_query, (request.user_id, group_id), commit=True)
        
        return jsonify({
            'message': 'Group created successfully',
            'group_id': group_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>/members', methods=['POST'])
@require_auth
def add_member(group_id):
    """Add a member to group"""
    try:
        data = request.get_json()
        
        # Verify user is creator
        check_query = """
            SELECT created_by FROM `Groups` WHERE group_id = %s
        """
        group = Database.execute_query(check_query, (group_id,), fetch_one=True)
        
        if not group:
            return jsonify({'error': 'Group not found'}), 404
        
        if group['created_by'] != request.user_id:
            return jsonify({'error': 'Only group creator can add members'}), 403
        
        # Find user by email
        user_query = "SELECT user_id FROM Users WHERE email = %s"
        user = Database.execute_query(user_query, (data.get('email'),), fetch_one=True)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if already member
        member_check = """
            SELECT user_id FROM User_Groups 
            WHERE group_id = %s AND user_id = %s
        """
        existing = Database.execute_query(
            member_check, (group_id, user['user_id']), fetch_one=True
        )
        
        if existing:
            return jsonify({'error': 'User is already a member'}), 409
        
        # Add member
        insert_query = """
            INSERT INTO User_Groups (user_id, group_id)
            VALUES (%s, %s)
        """
        Database.execute_query(insert_query, (user['user_id'], group_id), commit=True)
        
        return jsonify({'message': 'Member added successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>/members/<int:user_id>', methods=['DELETE'])
@require_auth
def remove_member(group_id, user_id):
    """Remove a member from group"""
    try:
        # Verify user is creator or removing themselves
        check_query = """
            SELECT created_by FROM `Groups` WHERE group_id = %s
        """
        group = Database.execute_query(check_query, (group_id,), fetch_one=True)
        
        if not group:
            return jsonify({'error': 'Group not found'}), 404
        
        is_creator = group['created_by'] == request.user_id
        is_self = user_id == request.user_id
        
        if not (is_creator or is_self):
            return jsonify({'error': 'You can only remove yourself or be the creator'}), 403
        
        # Don't allow removing creator
        if user_id == group['created_by']:
            return jsonify({'error': 'Cannot remove group creator'}), 400
        
        # Remove member
        delete_query = """
            DELETE FROM User_Groups 
            WHERE group_id = %s AND user_id = %s
        """
        Database.execute_query(delete_query, (group_id, user_id), commit=True)
        
        return jsonify({'message': 'Member removed successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_bp.route('/<int:group_id>', methods=['DELETE'])
@require_auth
def delete_group(group_id):
    """Delete a group (creator only)"""
    try:
        # Verify user is creator
        check_query = """
            SELECT created_by FROM `Groups` WHERE group_id = %s
        """
        group = Database.execute_query(check_query, (group_id,), fetch_one=True)
        
        if not group:
            return jsonify({'error': 'Group not found'}), 404
        
        if group['created_by'] != request.user_id:
            return jsonify({'error': 'Only group creator can delete group'}), 403
        
        # Delete group (cascade will handle User_Groups)
        delete_query = "DELETE FROM `Groups` WHERE group_id = %s"
        Database.execute_query(delete_query, (group_id,), commit=True)
        
        return jsonify({'message': 'Group deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@groups_bp.route('/<int:group_id>/expense-summary', methods=['GET'])
@require_auth
def get_group_expense_summary(group_id):
    """Get expense summary for a group using the View_Group_Expense_Summary view"""
    try:
        # Verify user is member
        member_check = """
            SELECT user_id FROM User_Groups 
            WHERE group_id = %s AND user_id = %s
        """
        is_member = Database.execute_query(
            member_check, (group_id, request.user_id), fetch_one=True
        )
        
        if not is_member:
            return jsonify({'error': 'You are not a member of this group'}), 403
        
        # Get expense summary from view
        summary_query = """
            SELECT 
                user_id, username, email,
                transaction_count, 
                total_expenses, 
                total_contributions,
                net_spending,
                fair_share,
                balance_owed
            FROM View_Group_Expense_Summary
            WHERE group_id = %s
            ORDER BY net_spending DESC
        """
        summary = Database.execute_query(summary_query, (group_id,), fetch_all=True)
        
        # Format decimal values
        for member in summary:
            member['total_expenses'] = float(member['total_expenses']) if member['total_expenses'] else 0.0
            member['total_contributions'] = float(member['total_contributions']) if member['total_contributions'] else 0.0
            member['net_spending'] = float(member['net_spending']) if member['net_spending'] else 0.0
            member['fair_share'] = float(member['fair_share']) if member['fair_share'] else 0.0
            member['balance_owed'] = float(member['balance_owed']) if member['balance_owed'] else 0.0
        
        # Get group total stats
        group_total = {
            'total_expenses': sum(m['total_expenses'] for m in summary),
            'total_contributions': sum(m['total_contributions'] for m in summary),
            'member_count': len(summary),
            'average_per_member': sum(m['total_expenses'] for m in summary) / len(summary) if summary else 0
        }
        
        return jsonify({
            'group_id': group_id,
            'members': summary,
            'group_total': group_total
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500