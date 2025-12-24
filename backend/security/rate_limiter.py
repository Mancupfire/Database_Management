"""
Rate limiting configuration for MoneyMinder
Protects against brute-force attacks and DoS attempts.
"""
from flask import jsonify, request
import os


class RateLimiterConfig:
    """Configuration for rate limiting"""
    DEFAULT_LIMIT = "100 per minute"
    LOGIN_LIMIT = "5 per 15 minutes"
    REGISTRATION_LIMIT = "3 per hour"
    STRICT_LIMIT = "10 per minute"


def get_remote_address():
    """Get the client's IP address, handling proxies."""
    # Check for forwarded header (when behind proxy)
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        # Take the first IP in the chain
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'


def init_rate_limiter(app):
    """
    Initialize rate limiter for the Flask application.
    
    Args:
        app: Flask application instance
        
    Returns:
        Limiter instance or None if Flask-Limiter not available
    """
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address as flask_get_remote_address
        
        # Use Redis in production, memory in development
        storage_uri = os.getenv('RATE_LIMIT_STORAGE', 'memory://')
        
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=[RateLimiterConfig.DEFAULT_LIMIT],
            storage_uri=storage_uri,
            strategy='fixed-window',
        )
        
        # Custom error handler for rate limit exceeded
        @app.errorhandler(429)
        def rate_limit_exceeded(e):
            from security.audit_logger import audit_logger
            
            # Log the rate limit event
            audit_logger.log_rate_limit(
                ip=get_remote_address(),
                endpoint=request.path,
                limit=str(e.description) if hasattr(e, 'description') else None
            )
            
            return jsonify({
                'error': 'Rate limit exceeded',
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': 'Too many requests. Please try again later.',
                'retry_after': getattr(e, 'retry_after', 60)
            }), 429
        
        return limiter
        
    except ImportError:
        # Flask-Limiter not installed
        import logging
        logging.warning("Flask-Limiter not installed. Rate limiting disabled.")
        return None


def rate_limit_login(limiter):
    """
    Decorator for login rate limiting.
    
    Args:
        limiter: Flask-Limiter instance
        
    Returns:
        Decorator function
    """
    if limiter is None:
        # No-op decorator if limiter not available
        def decorator(f):
            return f
        return decorator
    
    return limiter.limit(RateLimiterConfig.LOGIN_LIMIT)


def rate_limit_registration(limiter):
    """
    Decorator for registration rate limiting.
    
    Args:
        limiter: Flask-Limiter instance
        
    Returns:
        Decorator function
    """
    if limiter is None:
        def decorator(f):
            return f
        return decorator
    
    return limiter.limit(RateLimiterConfig.REGISTRATION_LIMIT)
