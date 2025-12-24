"""
Configuration validator for MoneyMinder
Validates security configuration at startup.
"""
import os
import secrets


class ConfigValidator:
    """Validates security configuration at startup"""
    
    MIN_JWT_SECRET_LENGTH = 32
    DEFAULT_SECRETS = [
        'your-jwt-secret-key-change-this-in-production',
        'your-secret-key-change-this-in-production',
        'secret',
        'changeme',
        '',
    ]
    
    @classmethod
    def validate_all(cls) -> tuple:
        """
        Validate all security configuration.
        
        Returns:
            Tuple of (is_valid: bool, errors: list[str])
        """
        errors = []
        
        # Validate JWT secret key
        jwt_secret = os.getenv('JWT_SECRET_KEY', '')
        
        if len(jwt_secret) < cls.MIN_JWT_SECRET_LENGTH:
            errors.append(
                f"JWT_SECRET_KEY must be at least {cls.MIN_JWT_SECRET_LENGTH} characters "
                f"(current: {len(jwt_secret)})"
            )
        
        if jwt_secret.lower() in [s.lower() for s in cls.DEFAULT_SECRETS]:
            errors.append("JWT_SECRET_KEY must be changed from default value")
        
        # Validate SECRET_KEY if present
        secret_key = os.getenv('SECRET_KEY', '')
        if secret_key and secret_key.lower() in [s.lower() for s in cls.DEFAULT_SECRETS]:
            errors.append("SECRET_KEY must be changed from default value")
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def generate_secure_key(length: int = 64) -> str:
        """
        Generate a cryptographically secure key.
        
        Args:
            length: Number of bytes (output will be longer due to base64 encoding)
            
        Returns:
            URL-safe base64 encoded random string
        """
        return secrets.token_urlsafe(length)
    
    @classmethod
    def validate_jwt_secret(cls, secret: str) -> tuple:
        """
        Validate a JWT secret key.
        
        Args:
            secret: The secret key to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str or None)
        """
        if not secret:
            return (False, "JWT_SECRET_KEY is required")
        
        if len(secret) < cls.MIN_JWT_SECRET_LENGTH:
            return (False, f"JWT_SECRET_KEY must be at least {cls.MIN_JWT_SECRET_LENGTH} characters")
        
        if secret.lower() in [s.lower() for s in cls.DEFAULT_SECRETS]:
            return (False, "JWT_SECRET_KEY must be changed from default value")
        
        return (True, None)
