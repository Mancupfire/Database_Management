"""
Configuration settings for MoneyMinder backend
"""
import os
from dotenv import load_dotenv

load_dotenv()

def _parse_origins(raw):
    """Return a list of origins from a comma-separated env string."""
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-please-change')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key-please-change')
    
    # Database configuration
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'moneyminder_app'),
        'password': os.getenv('DB_PASSWORD', 'MM_App@2024!r3set'),
        'database': os.getenv('DB_NAME', 'MoneyMinder_DB'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'charset': 'utf8mb4'
    }
    
    # Flask configuration
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    TESTING = False
    
    # Server configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # JWT configuration
    JWT_EXPIRATION_HOURS = 24

    # CORS configuration
    FRONTEND_ORIGINS = _parse_origins(os.getenv('FRONTEND_ORIGINS', 'http://localhost:8080'))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

# Config dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
