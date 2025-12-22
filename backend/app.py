"""
MoneyMinder Backend API
Flask application entry point
"""
from flask import Flask, jsonify
from flask_cors import CORS
from config import config
from database import Database
import atexit
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import route blueprints
from routes_auth import auth_bp
from routes_accounts import accounts_bp
from routes_transactions import transactions_bp
from routes_categories import categories_bp
from routes_analytics import analytics_bp
from routes_budgets import budgets_bp
from routes_groups import groups_bp
from routes_recurring import recurring_bp
from routes_notifications import notifications_bp
from routes_time import time_bp

# Import scheduler (optional)
try:
    from scheduler import start_scheduler, stop_scheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    logging.warning("APScheduler not available. Recurring payments will not be processed automatically.")

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Disable strict slashes to avoid redirect issues
    app.url_map.strict_slashes = False
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(recurring_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(time_bp)
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        db_status = Database.test_connection()
        return jsonify({
            'status': 'healthy' if db_status else 'unhealthy',
            'database': 'connected' if db_status else 'disconnected',
            'version': '1.0.0'
        }), 200 if db_status else 503
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint"""
        return jsonify({
            'message': 'MoneyMinder API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'auth': '/api/auth',
                'accounts': '/api/accounts',
                'transactions': '/api/transactions',
                'categories': '/api/categories',
                'analytics': '/api/analytics',
                'budgets': '/api/budgets',
                'groups': '/api/groups',
                'recurring': '/api/recurring'
            }
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("=" * 60)
    print("MoneyMinder Backend API Starting...")
    print(f"Environment: {app.config.get('ENV', 'development')}")
    print(f"Debug Mode: {app.config.get('DEBUG', False)}")
    print(f"Host: {app.config['HOST']}")
    print(f"Port: {app.config['PORT']}")
    print("=" * 60)
    
    # Test database connection
    if Database.test_connection():
        print("✓ Database connection successful!")
    else:
        print("✗ Database connection failed! Check your configuration.")
    
    print("=" * 60)
    print("API Documentation:")
    print("  POST   /api/auth/register      - Register new user")
    print("  POST   /api/auth/login         - Login user")
    print("  GET    /api/auth/me            - Get current user")
    print("  GET    /api/accounts           - List accounts")
    print("  POST   /api/accounts           - Create account")
    print("  GET    /api/transactions       - List transactions")
    print("  POST   /api/transactions       - Create transaction")
    print("  GET    /api/categories         - List categories")
    print("  GET    /api/analytics/dashboard - Get dashboard data")
    print("=" * 60)
    
    # Start background scheduler if available
    SCHEDULER_AVAILABLE = False  # Disabled scheduler
    if SCHEDULER_AVAILABLE:
        print("Starting background scheduler...")
        start_scheduler()
        print("✓ Scheduler started!")
        print("  - Recurring payments: Daily at 1:00 AM")
        print("  - Upcoming bills: Daily at 9:00 AM")
        print("  - Unusual spending: Every 6 hours")
        print("=" * 60)
        
        # Register cleanup on exit
        atexit.register(stop_scheduler)
    else:
        print("⚠ Scheduler not available (install APScheduler)")
        print("  Run: pip install APScheduler==3.10.4")
        print("=" * 60)
    
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
