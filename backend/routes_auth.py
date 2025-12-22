"""
Authentication routes
"""
from flask import Blueprint, request, jsonify
from database import Database
from auth import AuthManager

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if email already exists
        existing_user = Database.execute_query(
            "SELECT email FROM Users WHERE email = %s",
            (data['email'],),
            fetch_one=True
        )
        
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Hash password using bcrypt for security
        password_hash = AuthManager.hash_password(data['password'])
        
        # Insert new user
        user_id = Database.execute_query(
            """
            INSERT INTO Users (username, email, password_hash, base_currency)
            VALUES (%s, %s, %s, %s)
            """,
            (data['username'], data['email'], password_hash, data.get('base_currency', 'VND')),
            commit=True
        )
        
        # Generate token
        token = AuthManager.generate_token(user_id, data['username'], data['email'])
        
        return jsonify({
            'message': 'Registration successful',
            'token': token,
            'user': {
                'user_id': user_id,
                'username': data['username'],
                'email': data['email'],
                'base_currency': data.get('base_currency', 'VND')
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        # Get user from database
        user = Database.execute_query(
            """
            SELECT user_id, username, email, password_hash, base_currency
            FROM Users WHERE email = %s
            """,
            (data['email'],),
            fetch_one=True
        )
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password using bcrypt
        if not AuthManager.verify_password(data['password'], user['password_hash']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate token
        token = AuthManager.generate_token(
            user['user_id'],
            user['username'],
            user['email']
        )
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email'],
                'base_currency': user['base_currency']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user info (requires authentication)"""
    from auth import require_auth
    
    @require_auth
    def _get_user():
        try:
            user = Database.execute_query(
                """
                SELECT user_id, username, email, base_currency, created_at
                FROM Users WHERE user_id = %s
                """,
                (request.user_id,),
                fetch_one=True
            )
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify({'user': user}), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return _get_user()
