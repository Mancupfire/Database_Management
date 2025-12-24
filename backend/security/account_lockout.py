"""
Account lockout mechanism for MoneyMinder
Manages account lockout after failed login attempts.
"""
from datetime import datetime, timedelta


class AccountLockout:
    """Manages account lockout after failed login attempts"""
    
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    
    # In-memory storage for development (use database in production)
    _attempts = {}  # {email: [(timestamp, ip_address), ...]}
    
    @classmethod
    def record_failed_attempt(cls, email: str, ip_address: str) -> None:
        """
        Record a failed login attempt.
        
        Args:
            email: User email
            ip_address: Client IP address
        """
        if email not in cls._attempts:
            cls._attempts[email] = []
        
        cls._attempts[email].append({
            'timestamp': datetime.utcnow(),
            'ip_address': ip_address
        })
        
        # Clean up old attempts
        cls._cleanup_old_attempts(email)
    
    @classmethod
    def is_locked(cls, email: str) -> tuple:
        """
        Check if account is locked.
        
        Args:
            email: User email
            
        Returns:
            Tuple of (is_locked: bool, seconds_remaining: int)
        """
        if email not in cls._attempts:
            return (False, 0)
        
        cls._cleanup_old_attempts(email)
        
        recent_attempts = cls._attempts.get(email, [])
        
        if len(recent_attempts) >= cls.MAX_ATTEMPTS:
            # Get the oldest attempt in the window
            oldest = min(a['timestamp'] for a in recent_attempts)
            lockout_end = oldest + timedelta(minutes=cls.LOCKOUT_DURATION_MINUTES)
            
            if datetime.utcnow() < lockout_end:
                seconds_remaining = int((lockout_end - datetime.utcnow()).total_seconds())
                return (True, max(0, seconds_remaining))
        
        return (False, 0)
    
    @classmethod
    def reset_attempts(cls, email: str) -> None:
        """
        Reset failed attempts after successful login.
        
        Args:
            email: User email
        """
        if email in cls._attempts:
            del cls._attempts[email]
    
    @classmethod
    def get_attempt_count(cls, email: str) -> int:
        """
        Get the number of recent failed attempts.
        
        Args:
            email: User email
            
        Returns:
            Number of failed attempts in the lockout window
        """
        cls._cleanup_old_attempts(email)
        return len(cls._attempts.get(email, []))
    
    @classmethod
    def _cleanup_old_attempts(cls, email: str) -> None:
        """Remove attempts older than the lockout window."""
        if email not in cls._attempts:
            return
        
        cutoff = datetime.utcnow() - timedelta(minutes=cls.LOCKOUT_DURATION_MINUTES)
        cls._attempts[email] = [
            a for a in cls._attempts[email]
            if a['timestamp'] > cutoff
        ]
        
        if not cls._attempts[email]:
            del cls._attempts[email]
    
    @classmethod
    def cleanup_all_old_records(cls) -> int:
        """
        Remove all expired lockout records.
        
        Returns:
            Number of records cleaned up
        """
        cleaned = 0
        emails_to_remove = []
        
        for email in list(cls._attempts.keys()):
            original_count = len(cls._attempts[email])
            cls._cleanup_old_attempts(email)
            if email not in cls._attempts:
                cleaned += original_count
                emails_to_remove.append(email)
            else:
                cleaned += original_count - len(cls._attempts[email])
        
        return cleaned
