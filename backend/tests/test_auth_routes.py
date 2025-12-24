"""
Unit tests for authentication routes validation.
Tests registration and login validation.
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRegistrationValidation:
    """
    Tests for registration endpoint validation.
    Validates: Requirements 2.5, 3.4
    """
    
    def test_missing_required_fields(self, client):
        """Registration should fail with missing required fields."""
        # Missing all fields
        response = client.post('/api/auth/register', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'VALIDATION_ERROR'
        
        # Missing password
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com'
        })
        assert response.status_code == 400
    
    def test_invalid_email_format(self, client):
        """Registration should fail with invalid email format."""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'SecurePass1!'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'VALIDATION_ERROR'
        assert any(e['field'] == 'email' for e in data['details'])
    
    def test_invalid_username_format(self, client):
        """Registration should fail with invalid username format."""
        # Too short
        response = client.post('/api/auth/register', json={
            'username': 'ab',
            'email': 'test@example.com',
            'password': 'SecurePass1!'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert any(e['field'] == 'username' for e in data['details'])
        
        # Special characters
        response = client.post('/api/auth/register', json={
            'username': 'test@user',
            'email': 'test@example.com',
            'password': 'SecurePass1!'
        })
        assert response.status_code == 400
    
    def test_weak_password_rejected(self, client):
        """Registration should fail with weak password."""
        # Too short
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Short1!'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'VALIDATION_ERROR'
        assert any(e['field'] == 'password' for e in data['details'])
        
        # Missing uppercase
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'lowercase1!'
        })
        assert response.status_code == 400
        
        # Missing special character
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'NoSpecial123'
        })
        assert response.status_code == 400
    
    def test_password_containing_username_rejected(self, client):
        """Registration should fail if password contains username."""
        response = client.post('/api/auth/register', json={
            'username': 'johndoe',
            'email': 'john@example.com',
            'password': 'Johndoe123!'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert any('username' in e['message'].lower() for e in data['details'])


class TestLoginValidation:
    """
    Tests for login endpoint validation.
    """
    
    def test_missing_credentials(self, client):
        """Login should fail with missing credentials."""
        response = client.post('/api/auth/login', json={})
        assert response.status_code == 400
        
        response = client.post('/api/auth/login', json={'email': 'test@example.com'})
        assert response.status_code == 400
    
    def test_invalid_credentials(self, client):
        """Login should fail with invalid credentials."""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'WrongPass1!'
        })
        assert response.status_code == 401
        data = response.get_json()
        assert data['code'] == 'INVALID_CREDENTIALS'


class TestPasswordRequirementsEndpoint:
    """Tests for password requirements endpoint."""
    
    def test_get_password_requirements(self, client):
        """Should return password requirements."""
        response = client.get('/api/auth/password-requirements')
        assert response.status_code == 200
        data = response.get_json()
        assert 'requirements' in data
        assert 'min_length' in data
        assert data['min_length'] == 8


# Pytest fixtures
@pytest.fixture
def app():
    """Create test Flask application."""
    from flask import Flask
    from routes_auth import auth_bp
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(auth_bp)
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
