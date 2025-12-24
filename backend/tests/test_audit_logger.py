"""
Unit tests for audit logger.
Tests security event logging.
"""
import pytest
import os
import tempfile
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.audit_logger import AuditLogger, AuditEventType


class TestAuditLogger:
    """
    Tests for audit logger functionality.
    Validates: Requirements 8.1, 8.2, 8.4
    """
    
    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file for testing."""
        fd, path = tempfile.mkstemp(suffix='.log')
        os.close(fd)
        yield path
        # Cleanup
        if os.path.exists(path):
            os.remove(path)
    
    @pytest.fixture
    def logger(self, temp_log_file):
        """Create a fresh audit logger instance."""
        # Reset singleton
        AuditLogger._instance = None
        return AuditLogger(log_file=temp_log_file)
    
    def test_log_login_success(self, logger, temp_log_file):
        """
        Login success events should be logged with correct fields.
        Validates: Requirements 8.1
        """
        logger.log_login_attempt(
            email="test@example.com",
            ip="192.168.1.1",
            success=True,
            user_id=123
        )
        
        # Read log file
        with open(temp_log_file, 'r') as f:
            log_content = f.read()
        
        assert 'LOGIN_SUCCESS' in log_content
        assert 'test@example.com' in log_content
        assert '192.168.1.1' in log_content
        assert 'user_id=123' in log_content
    
    def test_log_login_failure(self, logger, temp_log_file):
        """
        Login failure events should be logged with correct fields.
        Validates: Requirements 8.1
        """
        logger.log_login_attempt(
            email="test@example.com",
            ip="192.168.1.1",
            success=False,
            reason="Invalid password"
        )
        
        # Read log file
        with open(temp_log_file, 'r') as f:
            log_content = f.read()
        
        assert 'LOGIN_FAILURE' in log_content
        assert 'test@example.com' in log_content
        assert '192.168.1.1' in log_content
        assert 'Invalid password' in log_content
    
    def test_log_account_locked(self, logger, temp_log_file):
        """
        Account lockout events should be logged.
        Validates: Requirements 8.2
        """
        logger.log_account_locked(
            email="test@example.com",
            ip="192.168.1.1",
            duration_minutes=15
        )
        
        # Read log file
        with open(temp_log_file, 'r') as f:
            log_content = f.read()
        
        assert 'ACCOUNT_LOCKED' in log_content
        assert 'test@example.com' in log_content
        assert '15' in log_content
    
    def test_log_rate_limit(self, logger, temp_log_file):
        """
        Rate limit events should be logged.
        Validates: Requirements 8.3
        """
        logger.log_rate_limit(
            ip="192.168.1.1",
            endpoint="/api/auth/login",
            limit="5 per 15 minutes"
        )
        
        # Read log file
        with open(temp_log_file, 'r') as f:
            log_content = f.read()
        
        assert 'RATE_LIMIT_EXCEEDED' in log_content
        assert '192.168.1.1' in log_content
        assert '/api/auth/login' in log_content
    
    def test_log_registration(self, logger, temp_log_file):
        """Registration events should be logged."""
        logger.log_registration(
            email="newuser@example.com",
            ip="192.168.1.1",
            user_id=456
        )
        
        # Read log file
        with open(temp_log_file, 'r') as f:
            log_content = f.read()
        
        assert 'REGISTRATION' in log_content
        assert 'newuser@example.com' in log_content
        assert 'user_id=456' in log_content
    
    def test_log_file_created(self, logger, temp_log_file):
        """
        Logs should be written to dedicated security log file.
        Validates: Requirements 8.4
        """
        logger.log_event(AuditEventType.LOGIN_SUCCESS, {'test': 'data'})
        
        assert os.path.exists(temp_log_file)
        
        with open(temp_log_file, 'r') as f:
            content = f.read()
        
        assert len(content) > 0
    
    def test_event_types(self):
        """All event types should be defined."""
        expected_types = [
            'LOGIN_SUCCESS',
            'LOGIN_FAILURE',
            'ACCOUNT_LOCKED',
            'ACCOUNT_UNLOCKED',
            'RATE_LIMIT_EXCEEDED',
            'REGISTRATION',
            'PASSWORD_CHANGE',
            'INVALID_TOKEN',
        ]
        
        for event_type in expected_types:
            assert hasattr(AuditEventType, event_type)


class TestAuditLoggerSingleton:
    """Tests for audit logger singleton behavior."""
    
    def test_singleton_pattern(self):
        """AuditLogger should be a singleton."""
        # Reset singleton
        AuditLogger._instance = None
        
        logger1 = AuditLogger()
        logger2 = AuditLogger()
        
        assert logger1 is logger2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
