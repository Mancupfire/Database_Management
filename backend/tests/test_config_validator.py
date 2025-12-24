"""
Property-based tests for configuration validator.
Tests JWT secret validation using Hypothesis.
"""
import pytest
from hypothesis import given, strategies as st, settings
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.config_validator import ConfigValidator


class TestJWTSecretValidation:
    """
    Property 12: Configuration Validation - JWT Secret Length
    For any JWT_SECRET_KEY configuration value, the configuration validator 
    SHALL reject it if the length is less than 32 characters.
    Validates: Requirements 7.2
    """
    
    @settings(max_examples=100)
    @given(st.text(min_size=0, max_size=31))
    def test_short_secrets_rejected(self, secret):
        """
        Feature: security-improvements, Property 12: Configuration Validation - JWT Secret Length
        Secrets shorter than 32 characters should be rejected.
        """
        is_valid, error = ConfigValidator.validate_jwt_secret(secret)
        assert not is_valid
        assert error is not None
    
    @settings(max_examples=100)
    @given(st.text(min_size=32, max_size=100, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P'),
        blacklist_characters='\x00'
    )))
    def test_long_enough_secrets_pass_length_check(self, secret):
        """
        Feature: security-improvements, Property 12: Configuration Validation - JWT Secret Length
        Secrets with 32+ characters should pass the length check.
        """
        # Skip default values
        if secret.lower() in [s.lower() for s in ConfigValidator.DEFAULT_SECRETS]:
            return
        
        is_valid, error = ConfigValidator.validate_jwt_secret(secret)
        # Should pass length check (may fail default value check)
        if not is_valid:
            assert "32 characters" not in error
    
    def test_default_secrets_rejected(self):
        """Default/placeholder secrets should be rejected."""
        default_secrets = [
            'your-jwt-secret-key-change-this-in-production',
            'secret',
            'changeme',
            '',
        ]
        for secret in default_secrets:
            is_valid, error = ConfigValidator.validate_jwt_secret(secret)
            assert not is_valid, f"Default secret '{secret}' should be rejected"
    
    def test_valid_secret_accepted(self):
        """A properly generated secret should be accepted."""
        # Generate a secure key
        secure_key = ConfigValidator.generate_secure_key(64)
        is_valid, error = ConfigValidator.validate_jwt_secret(secure_key)
        assert is_valid, f"Secure key should be valid but got error: {error}"
        assert error is None
    
    def test_generate_secure_key_length(self):
        """Generated keys should be sufficiently long."""
        key = ConfigValidator.generate_secure_key(32)
        # URL-safe base64 encoding produces ~4/3 the input length
        assert len(key) >= 32
        
        key = ConfigValidator.generate_secure_key(64)
        assert len(key) >= 64


class TestConfigValidatorAll:
    """Tests for validate_all method."""
    
    def test_validate_all_with_env(self, monkeypatch):
        """Test validate_all with environment variables."""
        # Set a valid JWT secret
        secure_key = ConfigValidator.generate_secure_key(64)
        monkeypatch.setenv('JWT_SECRET_KEY', secure_key)
        monkeypatch.delenv('SECRET_KEY', raising=False)
        
        is_valid, errors = ConfigValidator.validate_all()
        assert is_valid, f"Expected valid but got errors: {errors}"
        assert len(errors) == 0
    
    def test_validate_all_with_short_secret(self, monkeypatch):
        """Test validate_all with short JWT secret."""
        monkeypatch.setenv('JWT_SECRET_KEY', 'tooshort')
        
        is_valid, errors = ConfigValidator.validate_all()
        assert not is_valid
        assert any('32 characters' in e for e in errors)
    
    def test_validate_all_with_default_secret(self, monkeypatch):
        """Test validate_all with default JWT secret."""
        monkeypatch.setenv('JWT_SECRET_KEY', 'your-jwt-secret-key-change-this-in-production')
        
        is_valid, errors = ConfigValidator.validate_all()
        assert not is_valid
        assert any('default' in e.lower() for e in errors)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
