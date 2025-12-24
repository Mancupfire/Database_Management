"""
Property-based tests for security headers.
Tests that security headers are present on all responses.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSecurityHeaders:
    """
    Property 11: Security Headers Present
    For any API response, the response headers SHALL include X-Content-Type-Options, 
    X-Frame-Options, and X-XSS-Protection headers with correct values.
    Validates: Requirements 4.1, 4.2, 4.3
    """
    
    def test_x_content_type_options_header(self, client):
        """
        Feature: security-improvements, Property 11: Security Headers Present
        X-Content-Type-Options header should be present with value 'nosniff'.
        """
        response = client.get('/api/health')
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
    
    def test_x_frame_options_header(self, client):
        """
        Feature: security-improvements, Property 11: Security Headers Present
        X-Frame-Options header should be present with value 'DENY'.
        """
        response = client.get('/api/health')
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
    
    def test_x_xss_protection_header(self, client):
        """
        Feature: security-improvements, Property 11: Security Headers Present
        X-XSS-Protection header should be present.
        """
        response = client.get('/api/health')
        assert 'X-XSS-Protection' in response.headers
        assert '1' in response.headers['X-XSS-Protection']
    
    def test_content_security_policy_header(self, client):
        """Content-Security-Policy header should be present."""
        response = client.get('/api/health')
        assert 'Content-Security-Policy' in response.headers
        csp = response.headers['Content-Security-Policy']
        assert "default-src" in csp
    
    def test_referrer_policy_header(self, client):
        """Referrer-Policy header should be present."""
        response = client.get('/api/health')
        assert 'Referrer-Policy' in response.headers
    
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.sampled_from([
        '/api/health',
        '/api/auth/password-requirements',
        '/',
    ]))
    def test_headers_on_all_endpoints(self, client, endpoint):
        """
        Feature: security-improvements, Property 11: Security Headers Present
        Security headers should be present on all endpoints.
        """
        response = client.get(endpoint)
        
        # These headers should always be present
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers


# Pytest fixtures
@pytest.fixture
def app():
    """Create test Flask application with security headers."""
    from flask import Flask, jsonify
    from security.headers import init_security_headers
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Initialize security headers
    init_security_headers(app)
    
    # Add test endpoints
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    @app.route('/api/auth/password-requirements')
    def password_requirements():
        return jsonify({'min_length': 8})
    
    @app.route('/')
    def root():
        return jsonify({'message': 'MoneyMinder API'})
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
