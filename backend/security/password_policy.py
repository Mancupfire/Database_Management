"""
Password policy enforcement for MoneyMinder
Enforces password complexity requirements.
"""
import re


class PasswordPolicy:
    """Enforces password complexity requirements"""
    
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?~`'\"\\/"
    
    @classmethod
    def validate(cls, password: str, username: str = None, email: str = None) -> tuple:
        """
        Validate password against policy.
        
        Args:
            password: Password to validate
            username: Optional username to check against
            email: Optional email to check against
            
        Returns:
            Tuple of (is_valid: bool, errors: list[str])
        """
        errors = []
        
        if not password or not isinstance(password, str):
            return (False, ["Password is required"])
        
        # Length check
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters")
        
        # Uppercase check
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Lowercase check
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Digit check
        if cls.REQUIRE_DIGIT and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        # Special character check
        if cls.REQUIRE_SPECIAL and not any(c in cls.SPECIAL_CHARS for c in password):
            errors.append("Password must contain at least one special character")
        
        # Username exclusion check
        if username and username.lower() in password.lower():
            errors.append("Password cannot contain username")
        
        # Email exclusion check (local part before @)
        if email and '@' in email:
            email_local = email.split('@')[0].lower()
            if len(email_local) >= 3 and email_local in password.lower():
                errors.append("Password cannot contain email")
        
        return (len(errors) == 0, errors)
    
    @classmethod
    def get_requirements_text(cls) -> str:
        """Get human-readable password requirements."""
        requirements = [f"At least {cls.MIN_LENGTH} characters"]
        if cls.REQUIRE_UPPERCASE:
            requirements.append("At least one uppercase letter")
        if cls.REQUIRE_LOWERCASE:
            requirements.append("At least one lowercase letter")
        if cls.REQUIRE_DIGIT:
            requirements.append("At least one digit")
        if cls.REQUIRE_SPECIAL:
            requirements.append("At least one special character")
        return ", ".join(requirements)
