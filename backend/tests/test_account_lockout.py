"""
Property-based tests for account lockout.
Tests lockout mechanism using Hypothesis.
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.account_lockout import AccountLockout


class TestAccountLockoutAfterFailedAttempts:
    """
    Property 9: Account Lockout After Failed Attempts
    For any user account, if 5 consecutive failed login attempts occur, 
    the account SHALL be locked and subsequent login attempts SHALL fail 
    with lockout error until 15 minutes have elapsed.
    Validates: Requirements 5.1, 5.2
    """
    
    def setup_method(self):
        """Reset lockout state before each test."""
        AccountLockout._attempts = {}
    
    @settings(max_examples=50)
    @given(
        st.emails(),
        st.ip_addresses(v=4).map(str)
    )
    def test_account_locks_after_5_failures(self, email, ip):
        """
        Feature: security-improvements, Property 9: Account Lockout After Failed Attempts
        Account should lock after 5 failed attempts.
        """
        # Reset state
        AccountLockout._attempts = {}
        
        # Record 5 failed attempts
        for _ in range(5):
            AccountLockout.record_failed_attempt(email, ip)
        
        # Account should now be locked
        is_locked, seconds_remaining = AccountLockout.is_locked(email)
        assert is_locked, "Account should be locked after 5 failed attempts"
        assert seconds_remaining > 0, "Should have remaining lockout time"
    
    @settings(max_examples=50)
    @given(
        st.emails(),
        st.ip_addresses(v=4).map(str)
    )
    def test_account_not_locked_under_5_failures(self, email, ip):
        """
        Feature: security-improvements, Property 9: Account Lockout After Failed Attempts
        Account should not lock with fewer than 5 failed attempts.
        """
        # Reset state
        AccountLockout._attempts = {}
        
        # Record 4 failed attempts
        for _ in range(4):
            AccountLockout.record_failed_attempt(email, ip)
        
        # Account should NOT be locked
        is_locked, _ = AccountLockout.is_locked(email)
        assert not is_locked, "Account should not be locked with only 4 failed attempts"
    
    def test_lockout_duration(self):
        """Lockout should last for configured duration."""
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # Record 5 failed attempts
        for _ in range(5):
            AccountLockout.record_failed_attempt(email, ip)
        
        is_locked, seconds_remaining = AccountLockout.is_locked(email)
        assert is_locked
        # Should be close to 15 minutes (900 seconds)
        assert seconds_remaining <= AccountLockout.LOCKOUT_DURATION_MINUTES * 60
        assert seconds_remaining > 0


class TestAccountLockoutResetOnSuccess:
    """
    Property 10: Account Lockout Reset on Success
    For any user account with failed login attempts less than 5, 
    a successful login SHALL reset the failed attempt counter to zero.
    Validates: Requirements 5.4
    """
    
    def setup_method(self):
        """Reset lockout state before each test."""
        AccountLockout._attempts = {}
    
    @settings(max_examples=50)
    @given(
        st.emails(),
        st.ip_addresses(v=4).map(str),
        st.integers(min_value=1, max_value=4)
    )
    def test_reset_clears_attempts(self, email, ip, num_attempts):
        """
        Feature: security-improvements, Property 10: Account Lockout Reset on Success
        Successful login should reset failed attempt counter.
        """
        # Reset state
        AccountLockout._attempts = {}
        
        # Record some failed attempts (less than 5)
        for _ in range(num_attempts):
            AccountLockout.record_failed_attempt(email, ip)
        
        # Verify attempts were recorded
        assert AccountLockout.get_attempt_count(email) == num_attempts
        
        # Reset attempts (simulating successful login)
        AccountLockout.reset_attempts(email)
        
        # Verify attempts are cleared
        assert AccountLockout.get_attempt_count(email) == 0
        
        # Account should not be locked
        is_locked, _ = AccountLockout.is_locked(email)
        assert not is_locked
    
    def test_reset_after_lockout(self):
        """Reset should clear lockout state."""
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # Lock the account
        for _ in range(5):
            AccountLockout.record_failed_attempt(email, ip)
        
        is_locked, _ = AccountLockout.is_locked(email)
        assert is_locked
        
        # Reset attempts
        AccountLockout.reset_attempts(email)
        
        # Account should no longer be locked
        is_locked, _ = AccountLockout.is_locked(email)
        assert not is_locked


class TestAccountLockoutEdgeCases:
    """Edge case tests for account lockout."""
    
    def setup_method(self):
        """Reset lockout state before each test."""
        AccountLockout._attempts = {}
    
    def test_different_emails_independent(self):
        """Different email addresses should have independent lockout state."""
        email1 = "user1@example.com"
        email2 = "user2@example.com"
        ip = "192.168.1.1"
        
        # Lock email1
        for _ in range(5):
            AccountLockout.record_failed_attempt(email1, ip)
        
        # email1 should be locked
        is_locked1, _ = AccountLockout.is_locked(email1)
        assert is_locked1
        
        # email2 should NOT be locked
        is_locked2, _ = AccountLockout.is_locked(email2)
        assert not is_locked2
    
    def test_cleanup_removes_old_records(self):
        """Cleanup should remove expired records."""
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # Add some attempts
        for _ in range(3):
            AccountLockout.record_failed_attempt(email, ip)
        
        # Manually expire the attempts by modifying timestamps
        cutoff = datetime.utcnow() - timedelta(minutes=AccountLockout.LOCKOUT_DURATION_MINUTES + 1)
        for attempt in AccountLockout._attempts.get(email, []):
            attempt['timestamp'] = cutoff
        
        # Cleanup should remove them
        AccountLockout._cleanup_old_attempts(email)
        
        # Should have no attempts now
        assert AccountLockout.get_attempt_count(email) == 0
    
    def test_nonexistent_email_not_locked(self):
        """Non-existent email should not be locked."""
        is_locked, seconds = AccountLockout.is_locked("nonexistent@example.com")
        assert not is_locked
        assert seconds == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
