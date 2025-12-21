"""
Authentication utilities
"""
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from config import Config

class AuthManager:
    """Handles authentication and authorization"""
    
    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed):
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def generate_token(user_id, username, email, role):
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
    
    @staticmethod
    def decode_token(token):
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def get_token_from_request():
        """Extract token from request headers"""
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = AuthManager.get_token_from_request()
        
        if not token:
            return jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401
        
        payload = AuthManager.decode_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token', 'code': 'INVALID_TOKEN'}), 401
        
        # Add user info to request context
        request.user_id = payload['user_id']
        request.username = payload['username']
        request.email = payload['email']
        request.role = payload.get('role', 'user')
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(allowed_roles):
    """Decorator to require a specific role"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            token = AuthManager.get_token_from_request()
            if not token:
                return jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401
            payload = AuthManager.decode_token(token)
            if not payload:
                return jsonify({'error': 'Invalid or expired token', 'code': 'INVALID_TOKEN'}), 401
            role = payload.get('role', 'user')
            if role not in allowed_roles:
                return jsonify({'error': 'Forbidden', 'code': 'FORBIDDEN'}), 403
            request.user_id = payload['user_id']
            request.username = payload['username']
            request.email = payload['email']
            request.role = role
            return f(*args, **kwargs)
        return wrapped
    return decorator
