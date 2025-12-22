"""
Notifications routes
"""
from flask import Blueprint, request, jsonify
from database import Database
from auth import require_auth
from datetime import datetime, timedelta

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/', methods=['GET'])
@require_auth
def get_notifications():
    """Get user notifications from database"""
    try:
        # Get unread notifications first, then read ones, limited to last 50
        notifications_raw = Database.execute_query(
            """
            SELECT 
                notification_id, type, title, message, severity, 
                is_read, related_id, created_at
            FROM Notifications
            WHERE user_id = %s
            ORDER BY is_read ASC, created_at DESC
            LIMIT 50
            """,
            (request.user_id,),
            fetch_all=True
        )
        
        notifications = []
        for notif in notifications_raw:
            notifications.append({
                'id': notif['notification_id'],
                'type': notif['type'],
                'title': notif['title'],
                'message': notif['message'],
                'severity': notif['severity'],
                'is_read': bool(notif['is_read']),
                'related_id': notif['related_id'],
                'date': notif['created_at'].isoformat() if notif['created_at'] else None
            })
        
        return jsonify({
            'notifications': notifications,
            'count': len(notifications)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/summary', methods=['GET'])
@require_auth
def get_notification_summary():
    """Get notification counts by type"""
    try:
        # Count unread notifications
        unread_count = Database.execute_query(
            """
            SELECT COUNT(*) as count
            FROM Notifications
            WHERE user_id = %s AND is_read = FALSE
            """,
            (request.user_id,),
            fetch_one=True
        )
        
        # Count by type
        type_counts = Database.execute_query(
            """
            SELECT type, COUNT(*) as count
            FROM Notifications
            WHERE user_id = %s AND is_read = FALSE
            GROUP BY type
            """,
            (request.user_id,),
            fetch_all=True
        )
        
        counts_by_type = {item['type']: item['count'] for item in type_counts} if type_counts else {}
        
        return jsonify({
            'unread_count': unread_count['count'] if unread_count else 0,
            'upcoming_bills': counts_by_type.get('upcoming_bill', 0),
            'unusual_spending': counts_by_type.get('unusual_spending', 0),
            'budget_alerts': counts_by_type.get('budget_alert', 0),
            'total': unread_count['count'] if unread_count else 0
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@require_auth
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        Database.execute_query(
            """
            UPDATE Notifications
            SET is_read = TRUE
            WHERE notification_id = %s AND user_id = %s
            """,
            (notification_id, request.user_id),
            commit=True
        )
        
        return jsonify({'message': 'Notification marked as read'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/read-all', methods=['PUT'])
@require_auth
def mark_all_read():
    """Mark all notifications as read"""
    try:
        Database.execute_query(
            """
            UPDATE Notifications
            SET is_read = TRUE
            WHERE user_id = %s AND is_read = FALSE
            """,
            (request.user_id,),
            commit=True
        )
        
        return jsonify({'message': 'All notifications marked as read'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
