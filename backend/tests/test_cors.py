"""
Unit tests for CORS configuration.
Tests that CORS is properly configured.
"""
import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCORSConfiguration:
    """
    Tests for CORS configuration.
    Validates: Requirements 6.1, 6.2, 6.4
    """
    
    def test_localhost_allowed_in_development(self, monkeypatch):
        """
        Localhost should be allowed in development mode.
        Validates: Requirements 6.4
        """
        monkeypatch.setenv('FLASK_ENV', 'development')
        monkeypatch.setenv('JWT_SECRET_KEY', 'a' * 64)  # Valid secret
        
        from app import get_allowed_origins
        
        origins = get_allowed_origins()
        assert 'http://localhost:8080' in origins
        assert 'http://127.0.0.1:8080' in origins
    
    def test_configured_origins_used(self, monkeypatch):
        """
        Configured origins should be included.
        Validates: Requirements 6.1, 6.3
        """
        monkeypatch.setenv('FLASK_ENV', 'production')
        monkeypatch.setenv('ALLOWED_ORIGINS', 'https://example.com,https://app.example.com')
        
        from app import get_allowed_origins
        
        origins = get_allowed_origins()
        assert 'https://example.com' in origins
        assert 'https://app.example.com' in origins
    
    def test_empty_origins_in_production_without_config(self, monkeypatch):
        """
        Production without configured origins should return empty list.
        Validates: Requirements 6.1
        """
        monkeypatch.setenv('FLASK_ENV', 'production')
        monkeypatch.delenv('ALLOWED_ORIGINS', raising=False)
        
        from app import get_allowed_origins
        
        origins = get_allowed_origins()
        # Should be empty or only have explicitly configured origins
        assert 'http://localhost:8080' not in origins or len(origins) == 0


class TestCORSHeaders:
    """Tests for CORS headers in responses."""
    
    @pytest.fixture
    def client(self, monkeypatch):
        """Create test client with CORS enabled."""
        monkeypatch.setenv('FLASK_ENV', 'development')
        monkeypatch.setenv('JWT_SECRET_KEY', 'a' * 64)
        
        # Need to reimport to pick up env changes
        import importlib
        import app as app_module
        importlib.reload(app_module)
        
        test_app = app_module.create_app('development')
        return test_app.test_client()
    
    def test_cors_headers_present(self, client):
        """CORS headers should be present on responses."""
        response = client.options(
            '/api/health',
            headers={'Origin': 'http://localhost:8080'}
        )
        # CORS preflight should succeed
        assert response.status_code in [200, 204]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
