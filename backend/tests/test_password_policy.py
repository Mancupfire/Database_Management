"""
Property-based tests for password policy.
Tests password complexity requirements using Hypothesis.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
import string
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.password_policy import PasswordPolicy


class TestPasswordLengthRequirement:
    """
    Property 6: Password Policy - Length Requirement
    For any password string, the password policy SHALL reject it 
    if the length is less than 8 characters.
    Validates: Requirements 3.1
    """
    
    @settings(max_examples=100)
    @given(st.text(min_size=1, max_size=7))
    def test_short_passwords_rejected(self, password):
        """
        Feature: security-improvements, Property 6: Password Policy - Length Requirement
        Passwords shorter than 8 characters should be rejected.
        """
        is_valid, errors = PasswordPolicy.validate(password)
        assert not is_valid
        # Either "8 characters" error or "required" for empty-ish strings
        assert any("8 characters" in e or "required" in e.lower() for e in errors)
    
    @settings(max_examples=100)
    @given(st.text(min_size=8, max_size=50, alphabet=string.ascii_letters + string.digits + "!@#$%"))
    def test_long_enough_passwords_pass_length_check(self, password):
        """
        Feature: security-improvements, Property 6: Password Policy - Length Requirement
        Passwords with 8+ characters should pass the length check (may fail other checks).
        """
        is_valid, errors = PasswordPolicy.validate(password)
        # Should not have length error
        assert not any("8 characters" in e for e in errors)


class TestPasswordComplexityRequirements:
    """
    Property 7: Password Policy - Complexity Requirements
    For any password string, the password policy SHALL reject it if it lacks 
    at least one uppercase letter, one lowercase letter, one digit, or one special character.
    Validates: Requirements 3.2
    """
    
    @settings(max_examples=100)
    @given(st.text(min_size=8, max_size=20, alphabet=string.ascii_lowercase + string.digits + "!@#"))
    def test_missing_uppercase_rejected(self, password):
        """
        Feature: security-improvements, Property 7: Password Policy - Complexity Requirements
        Passwords without uppercase letters should be rejected.
        """
        assume(not any(c.isupper() for c in password))
        is_valid, errors = PasswordPolicy.validate(password)
        assert not is_valid
        assert any("uppercase" in e.lower() for e in errors)
    
    @settings(max_examples=100)
    @given(st.text(min_size=8, max_size=20, alphabet=string.ascii_uppercase + string.digits + "!@#"))
    def test_missing_lowercase_rejected(self, password):
        """
        Feature: security-improvements, Property 7: Password Policy - Complexity Requirements
        Passwords without lowercase letters should be rejected.
        """
        assume(not any(c.islower() for c in password))
        is_valid, errors = PasswordPolicy.validate(password)
        assert not is_valid
        assert any("lowercase" in e.lower() for e in errors)
    
    @settings(max_examples=100)
    @given(st.text(min_size=8, max_size=20, alphabet=string.ascii_letters + "!@#$%"))
    def test_missing_digit_rejected(self, password):
        """
        Feature: security-improvements, Property 7: Password Policy - Complexity Requirements
        Passwords without digits should be rejected.
        """
        assume(not any(c.isdigit() for c in password))
        is_valid, errors = PasswordPolicy.validate(password)
        assert not is_valid
        assert any("digit" in e.lower() for e in errors)
    
    @settings(max_examples=100)
    @given(st.text(min_size=8, max_size=20, alphabet=string.ascii_letters + string.digits))
    def test_missing_special_char_rejected(self, password):
        """
        Feature: security-improvements, Property 7: Password Policy - Complexity Requirements
        Passwords without special characters should be rejected.
        """
        special_chars = set(PasswordPolicy.SPECIAL_CHARS)
        assume(not any(c in special_chars for c in password))
        is_valid, errors = PasswordPolicy.validate(password)
        assert not is_valid
        assert any("special" in e.lower() for e in errors)
    
    def test_valid_password_accepted(self):
        """A password meeting all requirements should be accepted."""
        valid_passwords = [
            "Password1!",
            "Secure@123",
            "MyP@ssw0rd",
            "Test1234!",
            "Complex#Pass9",
        ]
        for password in valid_passwords:
            is_valid, errors = PasswordPolicy.validate(password)
            assert is_valid, f"Password '{password}' should be valid but got errors: {errors}"
            assert len(errors) == 0


class TestPasswordUsernameEmailExclusion:
    """
    Property 8: Password Policy - Username/Email Exclusion
    For any password string and associated username/email, the password policy 
    SHALL reject the password if it contains the username or the local part 
    of the email (case-insensitive).
    Validates: Requirements 3.3
    """
    
    @settings(max_examples=100)
    @given(
        st.from_regex(r'^[a-zA-Z0-9_]{3,10}$', fullmatch=True),
        st.sampled_from(['!', '@', '#', '$', '%']),
        st.integers(min_value=0, max_value=99)
    )
    def test_password_containing_username_rejected(self, username, special, num):
        """
        Feature: security-improvements, Property 8: Password Policy - Username/Email Exclusion
        Passwords containing the username should be rejected.
        """
        # Create a password that contains the username
        password = f"A{username}{special}{num}"
        
        # Ensure password meets other requirements
        if len(password) < 8:
            password = password + "x" * (8 - len(password))
        
        is_valid, errors = PasswordPolicy.validate(password, username=username)
        assert not is_valid
        assert any("username" in e.lower() for e in errors)
    
    @settings(max_examples=100)
    @given(
        st.from_regex(r'^[a-zA-Z0-9]{3,10}$', fullmatch=True),
        st.sampled_from(['gmail.com', 'example.com', 'test.org']),
        st.sampled_from(['!', '@', '#', '$', '%']),
        st.integers(min_value=0, max_value=99)
    )
    def test_password_containing_email_local_rejected(self, local_part, domain, special, num):
        """
        Feature: security-improvements, Property 8: Password Policy - Username/Email Exclusion
        Passwords containing the email local part should be rejected.
        """
        email = f"{local_part}@{domain}"
        # Create a password that contains the email local part
        password = f"A{local_part}{special}{num}"
        
        # Ensure password meets other requirements
        if len(password) < 8:
            password = password + "x" * (8 - len(password))
        
        is_valid, errors = PasswordPolicy.validate(password, email=email)
        assert not is_valid
        assert any("email" in e.lower() for e in errors)
    
    def test_password_not_containing_username_accepted(self):
        """Password not containing username should pass this check."""
        is_valid, errors = PasswordPolicy.validate(
            "Secure@123",
            username="johndoe"
        )
        assert is_valid
        assert not any("username" in e.lower() for e in errors)
    
    def test_password_not_containing_email_accepted(self):
        """Password not containing email local part should pass this check."""
        is_valid, errors = PasswordPolicy.validate(
            "Secure@123",
            email="johndoe@example.com"
        )
        assert is_valid
        assert not any("email" in e.lower() for e in errors)
    
    def test_case_insensitive_username_check(self):
        """Username check should be case-insensitive."""
        # Password contains "JOHN" but username is "john"
        is_valid, errors = PasswordPolicy.validate(
            "JOHN@1234",
            username="john"
        )
        assert not is_valid
        assert any("username" in e.lower() for e in errors)


class TestPasswordPolicyEdgeCases:
    """Edge case tests for password policy."""
    
    def test_empty_password_rejected(self):
        """Empty password should be rejected."""
        is_valid, errors = PasswordPolicy.validate("")
        assert not is_valid
    
    def test_none_password_rejected(self):
        """None password should be rejected."""
        is_valid, errors = PasswordPolicy.validate(None)
        assert not is_valid
    
    def test_whitespace_only_rejected(self):
        """Whitespace-only password should be rejected."""
        is_valid, errors = PasswordPolicy.validate("        ")
        assert not is_valid
    
    def test_requirements_text(self):
        """Requirements text should be generated correctly."""
        text = PasswordPolicy.get_requirements_text()
        assert "8 characters" in text
        assert "uppercase" in text.lower()
        assert "lowercase" in text.lower()
        assert "digit" in text.lower()
        assert "special" in text.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
