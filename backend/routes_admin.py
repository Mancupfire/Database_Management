"""
Admin-only routes
"""
from flask import Blueprint, jsonify
from auth import require_role

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/ping', methods=['GET'])
@require_role(['admin'])
def admin_ping():
    """Simple admin check endpoint"""
    return jsonify({'message': 'admin ok'}), 200
