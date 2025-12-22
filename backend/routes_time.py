"""
Time utility routes - provides server-side time
"""
from flask import Blueprint, jsonify
from datetime import datetime
from auth import require_auth

time_bp = Blueprint('time', __name__, url_prefix='/api/time')

@time_bp.route('/current', methods=['GET'])
@require_auth
def get_current_time():
    """Get current server time"""
    try:
        # Get current server time 
        from database import Database
        
        query = "SELECT NOW() as server_time"
        result = Database.execute_query(query, fetch_one=True)
        
        if result and result['server_time']:
            current_time = result['server_time']
            
            # Format for datetime-local input (YYYY-MM-DDTHH:mm)
            datetime_local = current_time.strftime('%Y-%m-%dT%H:%M')
            
            # Format for MySQL DATETIME (YYYY-MM-DD HH:MM:SS)
            mysql_format = current_time.strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({
                'datetime_local': datetime_local,  # For HTML datetime-local inputs
                'mysql_format': mysql_format,      # For API requests
                'timestamp': int(current_time.timestamp()),  # Unix timestamp
                'iso': current_time.isoformat()    # ISO format
            }), 200
        else:
            return jsonify({'error': 'Failed to get server time'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
