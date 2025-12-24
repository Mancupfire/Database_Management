"""
Authentication routes with security validation
"""
from flask import Blueprint, request, jsonify
from database import Database
from auth import AuthManager
from security.validators import InputValidator
from security.password_policy import PasswordPolicy
from security.account_lockout import AccountLockout
from security.audit_logger import audit_logger
from security.rate_limiter import get_remote_address

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user with input validation and password policy enforcement"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        if not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'code': 'VALIDATION_ERROR',
                'details': [{'field': f, 'message': f'{f} is required'} 
                           for f in required_fields if f not in data]
            }), 400
        
        validation_errors = []
        
        # Validate email format
        if not InputValidator.validate_email(data['email']):
            validation_errors.append({
                'field': 'email',
                'message': 'Invalid email format'
            })
        
        # Validate username format
        if not InputValidator.validate_username(data['username']):
            validation_errors.append({
                'field': 'username',
                'message': 'Username must be 3-50 characters, alphanumeric and underscores only'
            })
        
        # Validate password against policy
        password_valid, password_errors = PasswordPolicy.validate(
            data['password'],
            username=data['username'],
            email=data['email']
        )
        if not password_valid:
            for error in password_errors:
                validation_errors.append({
                    'field': 'password',
                    'message': error
                })
        
        # Return validation errors if any
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'code': 'VALIDATION_ERROR',
                'details': validation_errors
            }), 400
        
        # Check if email already exists
        existing_user = Database.execute_query(
            "SELECT email FROM Users WHERE email = %s",
            (data['email'],),
            fetch_one=True
        )
        
        if existing_user:
            return jsonify({
                'error': 'Email already registered',
                'code': 'EMAIL_EXISTS'
            }), 409
        
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
        
        # Log registration
        audit_logger.log_registration(
            email=data['email'],
            ip=get_remote_address(),
            user_id=user_id
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
    """Login user with account lockout protection"""
    try:
        data = request.get_json()
        ip_address = get_remote_address()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'error': 'Email and password required',
                'code': 'VALIDATION_ERROR'
            }), 400
        
        email = data['email']
        
        # Check if account is locked
        is_locked, seconds_remaining = AccountLockout.is_locked(email)
        if is_locked:
            audit_logger.log_login_attempt(
                email=email,
                ip=ip_address,
                success=False,
                reason='Account locked'
            )
            return jsonify({
                'error': 'Account temporarily locked due to too many failed attempts',
                'code': 'ACCOUNT_LOCKED',
                'retry_after': seconds_remaining
            }), 403
        
        # Get user from database
        user = Database.execute_query(
            """
            SELECT user_id, username, email, password_hash, base_currency
            FROM Users WHERE email = %s
            """,
            (email,),
            fetch_one=True
        )
        
        if not user:
            # Record failed attempt
            AccountLockout.record_failed_attempt(email, ip_address)
            audit_logger.log_login_attempt(
                email=email,
                ip=ip_address,
                success=False,
                reason='User not found'
            )
            
            # Check if now locked
            is_locked, seconds_remaining = AccountLockout.is_locked(email)
            if is_locked:
                audit_logger.log_account_locked(email, ip_address, AccountLockout.LOCKOUT_DURATION_MINUTES)
            
            return jsonify({
                'error': 'Invalid credentials',
                'code': 'INVALID_CREDENTIALS'
            }), 401
        
        # Verify password using bcrypt
        if not AuthManager.verify_password(data['password'], user['password_hash']):
            # Record failed attempt
            AccountLockout.record_failed_attempt(email, ip_address)
            audit_logger.log_login_attempt(
                email=email,
                ip=ip_address,
                success=False,
                reason='Invalid password'
            )
            
            # Check if now locked
            is_locked, seconds_remaining = AccountLockout.is_locked(email)
            if is_locked:
                audit_logger.log_account_locked(email, ip_address, AccountLockout.LOCKOUT_DURATION_MINUTES)
                return jsonify({
                    'error': 'Account temporarily locked due to too many failed attempts',
                    'code': 'ACCOUNT_LOCKED',
                    'retry_after': seconds_remaining
                }), 403
            
            return jsonify({
                'error': 'Invalid credentials',
                'code': 'INVALID_CREDENTIALS'
            }), 401
        
        # Successful login - reset failed attempts
        AccountLockout.reset_attempts(email)
        audit_logger.log_login_attempt(
            email=email,
            ip=ip_address,
            success=True,
            user_id=user['user_id']
        )
        
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


@auth_bp.route('/password-requirements', methods=['GET'])
def get_password_requirements():
    """Get password policy requirements"""
    return jsonify({
        'requirements': PasswordPolicy.get_requirements_text(),
        'min_length': PasswordPolicy.MIN_LENGTH,
        'require_uppercase': PasswordPolicy.REQUIRE_UPPERCASE,
        'require_lowercase': PasswordPolicy.REQUIRE_LOWERCASE,
        'require_digit': PasswordPolicy.REQUIRE_DIGIT,
        'require_special': PasswordPolicy.REQUIRE_SPECIAL
    }), 200
