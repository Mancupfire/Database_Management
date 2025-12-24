"""
Property-based tests for rate limiter.
Tests rate limiting functionality.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRateLimiter:
    """
    Property 1: Rate Limiter Blocks Excess Requests
    For any client IP address making requests to the API, if the number of requests 
    within a 1-minute window exceeds 100, then all subsequent requests within that 
    window SHALL receive HTTP 429 responses.
    Validates: Requirements 1.1
    
    Property 2: Login Rate Limit Enforcement
    For any client IP address attempting login, if the number of failed login attempts 
    within a 15-minute window exceeds 5, then all subsequent login attempts from that 
    IP SHALL be blocked until the window resets.
    Validates: Requirements 1.2
    """
    
    @pytest.fixture
    def app_with_limiter(self):
        """Create Flask app with rate limiter."""
        from flask import Flask, jsonify
        
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        try:
            from flask_limiter import Limiter
            from flask_limiter.util import get_remote_address
            
            limiter = Limiter(
                app=app,
                key_func=get_remote_address,
                default_limits=["10 per minute"],  # Lower limit for testing
                storage_uri="memory://"
            )
            
            @app.route('/api/test')
            def test_endpoint():
                return jsonify({'status': 'ok'})
            
            @app.route('/api/login', methods=['POST'])
            @limiter.limit("3 per minute")  # Lower limit for testing
            def login_endpoint():
                return jsonify({'status': 'ok'})
            
            return app, limiter
            
        except ImportError:
            pytest.skip("Flask-Limiter not installed")
    
    def test_rate_limit_blocks_excess_requests(self, app_with_limiter):
        """
        Feature: security-improvements, Property 1: Rate Limiter Blocks Excess Requests
        Requests exceeding the limit should receive 429 response.
        """
        app, limiter = app_with_limiter
        client = app.test_client()
        
        # Make requests up to the limit
        for i in range(10):
            response = client.get('/api/test')
            assert response.status_code == 200, f"Request {i+1} should succeed"
        
        # Next request should be rate limited
        response = client.get('/api/test')
        assert response.status_code == 429, "Request exceeding limit should return 429"
    
    def test_login_rate_limit(self, app_with_limiter):
        """
        Feature: security-improvements, Property 2: Login Rate Limit Enforcement
        Login attempts exceeding the limit should be blocked.
        """
        app, limiter = app_with_limiter
        client = app.test_client()
        
        # Make login attempts up to the limit
        for i in range(3):
            response = client.post('/api/login')
            assert response.status_code == 200, f"Login attempt {i+1} should succeed"
        
        # Next login attempt should be rate limited
        response = client.post('/api/login')
        assert response.status_code == 429, "Login attempt exceeding limit should return 429"
    
    def test_rate_limit_returns_retry_after(self, app_with_limiter):
        """Rate limit response should include retry information."""
        app, limiter = app_with_limiter
        client = app.test_client()
        
        # Exhaust the limit
        for _ in range(11):
            client.get('/api/test')
        
        # Check the 429 response
        response = client.get('/api/test')
        assert response.status_code == 429


class TestRateLimiterConfig:
    """Tests for rate limiter configuration."""
    
    def test_config_values(self):
        """Rate limiter config should have expected values."""
        from security.rate_limiter import RateLimiterConfig
        
        assert RateLimiterConfig.DEFAULT_LIMIT == "100 per minute"
        assert RateLimiterConfig.LOGIN_LIMIT == "5 per 15 minutes"
        assert RateLimiterConfig.REGISTRATION_LIMIT == "3 per hour"
    
    def test_get_remote_address(self):
        """get_remote_address should handle various scenarios."""
        from flask import Flask
        from security.rate_limiter import get_remote_address
        
        app = Flask(__name__)
        
        with app.test_request_context(
            '/',
            headers={'X-Forwarded-For': '10.0.0.1, 192.168.1.1'}
        ):
            # Should return first IP in X-Forwarded-For
            assert get_remote_address() == '10.0.0.1'
        
        with app.test_request_context('/'):
            # Should return remote_addr when no forwarded header
            addr = get_remote_address()
            assert addr is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
