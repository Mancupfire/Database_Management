"""
Security audit logging for MoneyMinder
Logs security-relevant events for monitoring and investigation.
"""
import logging
import os
from datetime import datetime
from enum import Enum


class AuditEventType(Enum):
    """Types of security audit events"""
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    REGISTRATION = "REGISTRATION"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    INVALID_TOKEN = "INVALID_TOKEN"


class AuditLogger:
    """Logs security-relevant events"""
    
    _instance = None
    
    def __new__(cls, log_file: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_file: str = None):
        if self._initialized:
            return
        
        self._initialized = True
        
        # Default log file location
        if log_file is None:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'security_audit.log')
        
        self.log_file = log_file
        
        # Create dedicated security logger
        self.logger = logging.getLogger("security_audit")
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers = []
        
        # File handler - always add
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(event_type)s] %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
        # Also log to console in development
        if os.getenv('FLASK_ENV', 'development') == 'development':
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - SECURITY - [%(event_type)s] %(message)s'
            ))
            self.logger.addHandler(console_handler)
    
    def log_event(self, event_type: AuditEventType, details: dict) -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            details: Dictionary of event details
        """
        extra = {'event_type': event_type.value}
        message = ' | '.join(f"{k}={v}" for k, v in details.items())
        self.logger.info(message, extra=extra)
    
    def log_login_attempt(self, email: str, ip: str, success: bool, 
                          user_id: int = None, reason: str = None) -> None:
        """
        Log a login attempt.
        
        Args:
            email: User email
            ip: Client IP address
            success: Whether login was successful
            user_id: User ID if login was successful
            reason: Reason for failure if unsuccessful
        """
        event_type = AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE
        details = {
            'email': email,
            'ip_address': ip,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        if user_id:
            details['user_id'] = user_id
        if reason:
            details['reason'] = reason
        
        self.log_event(event_type, details)
    
    def log_account_locked(self, email: str, ip: str, duration_minutes: int) -> None:
        """
        Log an account lockout event.
        
        Args:
            email: User email
            ip: Client IP address that triggered lockout
            duration_minutes: Lockout duration in minutes
        """
        self.log_event(AuditEventType.ACCOUNT_LOCKED, {
            'email': email,
            'ip_address': ip,
            'duration_minutes': duration_minutes,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def log_rate_limit(self, ip: str, endpoint: str, limit: str = None) -> None:
        """
        Log a rate limit exceeded event.
        
        Args:
            ip: Client IP address
            endpoint: API endpoint that was rate limited
            limit: The limit that was exceeded
        """
        details = {
            'ip_address': ip,
            'endpoint': endpoint,
            'timestamp': datetime.utcnow().isoformat()
        }
        if limit:
            details['limit'] = limit
        
        self.log_event(AuditEventType.RATE_LIMIT_EXCEEDED, details)
    
    def log_registration(self, email: str, ip: str, user_id: int) -> None:
        """
        Log a new user registration.
        
        Args:
            email: User email
            ip: Client IP address
            user_id: New user's ID
        """
        self.log_event(AuditEventType.REGISTRATION, {
            'email': email,
            'ip_address': ip,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        })


# Global audit logger instance
audit_logger = AuditLogger()
