"""
Input validation utilities for MoneyMinder
Provides validation for emails, usernames, amounts, and string lengths.
"""
import re
from functools import wraps
from flask import request, jsonify
from decimal import Decimal, InvalidOperation


class ValidationError(Exception):
    """Exception raised when input validation fails"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class InputValidator:
    """Validates and sanitizes user input"""
    
    # RFC 5322 compliant email regex (simplified but practical)
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Username: alphanumeric + underscore, 3-50 characters
    USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{3,50}$')
    
    # Field length limits matching database schema
    FIELD_LIMITS = {
        'username': 50,
        'email': 100,
        'password': 255,
        'account_name': 50,
        'category_name': 50,
        'group_name': 100,
        'currency_code': 3,
        'base_currency': 3,
    }
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format against RFC 5322 standard.
        
        Args:
            email: Email string to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False
        return bool(InputValidator.EMAIL_REGEX.match(email.strip()))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate username format.
        Must contain only alphanumeric characters and underscores,
        and be between 3-50 characters.
        
        Args:
            username: Username string to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not username or not isinstance(username, str):
            return False
        return bool(InputValidator.USERNAME_REGEX.match(username))
    
    @staticmethod
    def validate_amount(amount) -> bool:
        """
        Validate transaction amount.
        Must be a positive number with at most 2 decimal places.
        
        Args:
            amount: Amount to validate (can be int, float, str, or Decimal)
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Convert to Decimal for precise validation
            if isinstance(amount, str):
                dec_amount = Decimal(amount)
            elif isinstance(amount, (int, float)):
                dec_amount = Decimal(str(amount))
            elif isinstance(amount, Decimal):
                dec_amount = amount
            else:
                return False
            
            # Must be positive
            if dec_amount <= 0:
                return False
            
            # Check decimal places (at most 2)
            # Get the exponent - negative exponent means decimal places
            sign, digits, exponent = dec_amount.as_tuple()
            if exponent < -2:
                return False
            
            return True
            
        except (InvalidOperation, ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_string_length(value: str, field_name: str = None, max_length: int = None) -> bool:
        """
        Validate string doesn't exceed maximum length.
        
        Args:
            value: String to validate
            field_name: Optional field name to look up limit in FIELD_LIMITS
            max_length: Optional explicit max length (overrides field_name lookup)
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(value, str):
            return False
        
        # Determine max length
        if max_length is not None:
            limit = max_length
        elif field_name and field_name in InputValidator.FIELD_LIMITS:
            limit = InputValidator.FIELD_LIMITS[field_name]
        else:
            # No limit specified, accept any length
            return True
        
        return len(value) <= limit
    
    @staticmethod
    def validate_field(value, field_name: str, field_type: str = 'string') -> tuple[bool, str]:
        """
        Validate a field based on its type.
        
        Args:
            value: Value to validate
            field_name: Name of the field
            field_type: Type of validation ('email', 'username', 'amount', 'string')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if field_type == 'email':
            if not InputValidator.validate_email(value):
                return False, f"Invalid email format"
        elif field_type == 'username':
            if not InputValidator.validate_username(value):
                return False, f"Username must be 3-50 characters, alphanumeric and underscores only"
        elif field_type == 'amount':
            if not InputValidator.validate_amount(value):
                return False, f"Amount must be a positive number with at most 2 decimal places"
        elif field_type == 'string':
            if not InputValidator.validate_string_length(value, field_name):
                limit = InputValidator.FIELD_LIMITS.get(field_name, 'unknown')
                return False, f"Field exceeds maximum length of {limit} characters"
        
        return True, ""


def validate_request(schema: dict):
    """
    Decorator to validate request JSON against a schema.
    
    Schema format:
    {
        'field_name': {
            'type': 'email' | 'username' | 'amount' | 'string',
            'required': True | False,
            'max_length': int (optional, for strings)
        }
    }
    
    Example:
        @validate_request({
            'email': {'type': 'email', 'required': True},
            'username': {'type': 'username', 'required': True},
            'amount': {'type': 'amount', 'required': False}
        })
        def my_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() or {}
            errors = []
            
            for field_name, rules in schema.items():
                value = data.get(field_name)
                required = rules.get('required', False)
                field_type = rules.get('type', 'string')
                max_length = rules.get('max_length')
                
                # Check required fields
                if required and (value is None or value == ''):
                    errors.append({'field': field_name, 'message': f'{field_name} is required'})
                    continue
                
                # Skip validation if field is not present and not required
                if value is None or value == '':
                    continue
                
                # Validate based on type
                is_valid, error_msg = InputValidator.validate_field(value, field_name, field_type)
                if not is_valid:
                    errors.append({'field': field_name, 'message': error_msg})
                
                # Additional length check if specified
                if max_length and isinstance(value, str) and len(value) > max_length:
                    errors.append({
                        'field': field_name, 
                        'message': f'{field_name} exceeds maximum length of {max_length}'
                    })
            
            if errors:
                return jsonify({
                    'error': 'Validation failed',
                    'code': 'VALIDATION_ERROR',
                    'details': errors
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
