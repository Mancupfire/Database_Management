"""
Integration tests for complete security flow.
Tests that all security components work together.
"""
import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSecurityIntegration:
    """
    Integration tests for security features.
    Tests registration, login, lockout, and headers together.
    """
    
    @pytest.fixture
    def app(self, monkeypatch):
        """Create test application with all security features."""
        monkeypatch.setenv('FLASK_ENV', 'development')
        monkeypatch.setenv('JWT_SECRET_KEY', 'a' * 64)
        
        # Reimport to pick up env changes
        import importlib
        import app as app_module
        importlib.reload(app_module)
        
        return app_module.create_app('development')
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_registration_with_validation(self, client):
        """
        Registration should validate all inputs.
        Tests: Input validation, password policy
        """
        # Invalid email
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'SecurePass1!'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'email' in str(data)
        
        # Weak password
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'weak'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'password' in str(data).lower()
    
    def test_security_headers_on_all_responses(self, client):
        """
        Security headers should be present on all responses.
        Tests: Security headers
        """
        endpoints = [
            ('GET', '/api/health'),
            ('GET', '/'),
            ('POST', '/api/auth/login'),
        ]
        
        for method, endpoint in endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            # Check security headers
            assert 'X-Content-Type-Options' in response.headers, f"Missing header on {endpoint}"
            assert 'X-Frame-Options' in response.headers, f"Missing header on {endpoint}"
    
    def test_login_validation(self, client):
        """
        Login should validate inputs and return proper errors.
        Tests: Input validation, error handling
        """
        # Missing credentials
        response = client.post('/api/auth/login', json={})
        assert response.status_code == 400
        
        # Invalid credentials
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'WrongPass1!'
        })
        assert response.status_code == 401
        data = response.get_json()
        assert data['code'] == 'INVALID_CREDENTIALS'
    
    def test_password_requirements_endpoint(self, client):
        """Password requirements endpoint should return policy details."""
        response = client.get('/api/auth/password-requirements')
        assert response.status_code == 200
        data = response.get_json()
        assert 'min_length' in data
        assert data['min_length'] == 8


class TestSecurityComponentsLoaded:
    """Tests that all security components are properly loaded."""
    
    def test_all_security_modules_importable(self):
        """All security modules should be importable."""
        from security import (
            InputValidator,
            ValidationError,
            validate_request,
            PasswordPolicy,
            ConfigValidator,
            init_security_headers,
            AccountLockout,
            AuditLogger,
            AuditEventType,
            init_rate_limiter,
            RateLimiterConfig,
        )
        
        # Verify classes exist
        assert InputValidator is not None
        assert PasswordPolicy is not None
        assert ConfigValidator is not None
        assert AccountLockout is not None
        assert AuditLogger is not None
    
    def test_validators_work(self):
        """Validators should work correctly."""
        from security.validators import InputValidator
        
        assert InputValidator.validate_email('test@example.com') == True
        assert InputValidator.validate_email('invalid') == False
        assert InputValidator.validate_username('valid_user') == True
        assert InputValidator.validate_username('ab') == False
        assert InputValidator.validate_amount(100.50) == True
        assert InputValidator.validate_amount(-10) == False
    
    def test_password_policy_works(self):
        """Password policy should work correctly."""
        from security.password_policy import PasswordPolicy
        
        # Valid password
        is_valid, errors = PasswordPolicy.validate('SecurePass1!')
        assert is_valid
        assert len(errors) == 0
        
        # Invalid password
        is_valid, errors = PasswordPolicy.validate('weak')
        assert not is_valid
        assert len(errors) > 0
    
    def test_account_lockout_works(self):
        """Account lockout should work correctly."""
        from security.account_lockout import AccountLockout
        
        # Reset state
        AccountLockout._attempts = {}
        
        email = 'test@example.com'
        ip = '192.168.1.1'
        
        # Should not be locked initially
        is_locked, _ = AccountLockout.is_locked(email)
        assert not is_locked
        
        # Record 5 failures
        for _ in range(5):
            AccountLockout.record_failed_attempt(email, ip)
        
        # Should be locked now
        is_locked, _ = AccountLockout.is_locked(email)
        assert is_locked
        
        # Reset
        AccountLockout.reset_attempts(email)
        is_locked, _ = AccountLockout.is_locked(email)
        assert not is_locked


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
