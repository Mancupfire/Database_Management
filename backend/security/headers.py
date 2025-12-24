"""
Security headers configuration for MoneyMinder
Configures HTTP security headers using Flask-Talisman.
"""
import os


def init_security_headers(app):
    """
    Initialize security headers for the Flask application.
    
    Uses Flask-Talisman if available, otherwise sets headers manually.
    
    Args:
        app: Flask application instance
    """
    try:
        from flask_talisman import Talisman
        
        # Content Security Policy
        csp = {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline'",
            'style-src': "'self' 'unsafe-inline'",
            'img-src': "'self' data:",
            'font-src': "'self'",
            'connect-src': "'self'",
        }
        
        # Check if we're in development mode
        is_development = os.getenv('FLASK_ENV', 'development') == 'development'
        force_https = not is_development and os.getenv('FORCE_HTTPS', 'false').lower() == 'true'
        
        Talisman(
            app,
            force_https=force_https,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,  # 1 year
            strict_transport_security_include_subdomains=True,
            content_security_policy=csp,
            frame_options='DENY',
            x_content_type_options=True,
            x_xss_protection=True,
            referrer_policy='strict-origin-when-cross-origin',
        )
        
    except ImportError:
        # Flask-Talisman not installed, set headers manually
        @app.after_request
        def set_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Only set HSTS if using HTTPS
            if os.getenv('FORCE_HTTPS', 'false').lower() == 'true':
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            # Basic CSP
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'"
            )
            
            return response
