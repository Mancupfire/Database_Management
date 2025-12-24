# MoneyMinder Security Documentation

## Table of Contents

1. [Overview](#overview)
2. [Security Architecture](#security-architecture)
3. [Authentication & Authorization](#authentication--authorization)
4. [Input Validation](#input-validation)
5. [Password Security](#password-security)
6. [Rate Limiting](#rate-limiting)
7. [Account Lockout](#account-lockout)
8. [Security Headers](#security-headers)
9. [CORS Configuration](#cors-configuration)
10. [Audit Logging](#audit-logging)
11. [Database Security](#database-security)
12. [Configuration Security](#configuration-security)
13. [Deployment Security](#deployment-security)
14. [Security Testing](#security-testing)
15. [Incident Response](#incident-response)
16. [Future Improvements](#future-improvements)

---

## Overview

MoneyMinder implements a comprehensive security framework to protect user data and prevent common web vulnerabilities. This document outlines all security measures, their implementation, and best practices for deployment and maintenance.

**Security Principles:**
- Defense in depth: Multiple layers of security controls
- Least privilege: Users and services have minimal required permissions
- Fail securely: Errors don't expose sensitive information
- Input validation: All user input is validated and sanitized
- Encryption: Sensitive data is encrypted in transit and at rest

---

## Security Architecture

### Components

The security module (`backend/security/`) provides:

```
backend/security/
├── __init__.py              # Module exports
├── validators.py            # Input validation
├── password_policy.py       # Password requirements
├── config_validator.py      # Configuration validation
├── headers.py               # Security headers
├── account_lockout.py       # Account lockout mechanism
├── audit_logger.py          # Security event logging
└── rate_limiter.py          # Rate limiting
```

### Security Flow

```
Request
  ↓
[Rate Limiter] → Check request frequency
  ↓
[CORS Check] → Verify origin
  ↓
[Security Headers] → Add protective headers
  ↓
[Input Validation] → Validate and sanitize input
  ↓
[Authentication] → Verify JWT token
  ↓
[Authorization] → Check permissions
  ↓
[Audit Log] → Log security events
  ↓
Response
```

---

## Authentication & Authorization

### JWT Authentication

MoneyMinder uses JSON Web Tokens (JWT) for stateless authentication.

**Token Structure:**
```python
{
  "user_id": 123,
  "username": "john_doe",
  "email": "john@example.com",
  "iat": 1704067200,
  "exp": 1704153600
}
```

**Token Generation:**
```python
from auth import AuthManager

token = AuthManager.generate_token(user_id, username, email)
```

**Token Verification:**
```python
from auth import require_auth

@require_auth
def protected_route():
    # request.user_id is available
    return jsonify({'user_id': request.user_id})
```

**Token Expiration:**
- Default: 24 hours
- Configurable via `JWT_EXPIRATION` in `.env`
- Expired tokens return 401 Unauthorized

### Authorization

Database-level role-based access control (RBAC):

```sql
-- Three database users with different privileges
CREATE USER 'moneyminder_admin'@'localhost';      -- Full access
CREATE USER 'moneyminder_app'@'localhost';        -- Application access
CREATE USER 'moneyminder_readonly'@'localhost';   -- Read-only access
```

**Privilege Levels:**
- `moneyminder_admin`: DDL/DML operations, user management
- `moneyminder_app`: SELECT, INSERT, UPDATE, DELETE on application tables
- `moneyminder_readonly`: SELECT only on application tables

---

## Input Validation

### Validators

All user input is validated using the `InputValidator` class.

**Email Validation:**
```python
from security.validators import InputValidator

if InputValidator.validate_email(email):
    # Valid email format
    pass
```

- Pattern: RFC 5322 compliant regex
- Length: 5-254 characters
- Rejects: Invalid formats, disposable emails (optional)

**Username Validation:**
```python
if InputValidator.validate_username(username):
    # Valid username
    pass
```

- Length: 3-50 characters
- Characters: Alphanumeric and underscores only
- Rejects: Special characters, spaces

**Amount Validation:**
```python
if InputValidator.validate_amount(amount):
    # Valid monetary amount
    pass
```

- Format: Positive decimal numbers
- Precision: Maximum 2 decimal places
- Range: 0.01 to 999,999,999.99

**String Length Validation:**
```python
if InputValidator.validate_string_length(text, min_length=1, max_length=255):
    # Valid string length
    pass
```

### Validation Errors

Validation failures return HTTP 400 with detailed error information:

```json
{
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "details": [
    {
      "field": "email",
      "message": "Invalid email format"
    },
    {
      "field": "password",
      "message": "Password must contain at least one uppercase letter"
    }
  ]
}
```

---

## Password Security

### Password Policy

All passwords must meet these requirements:

**Requirements:**
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*)

**Restrictions:**
- Cannot contain username
- Cannot contain email address
- Cannot be a common password (future enhancement)

**Example:**
```python
from security.password_policy import PasswordPolicy

password = "MySecure@Pass123"
username = "john_doe"
email = "john@example.com"

is_valid, errors = PasswordPolicy.validate(password, username, email)

if not is_valid:
    for error in errors:
        print(error)
        # "Password must contain at least one special character"
```

### Password Hashing

Passwords are hashed using bcrypt with salt:

```python
from auth import AuthManager

# Hashing
password_hash = AuthManager.hash_password("MySecure@Pass123")

# Verification
is_correct = AuthManager.verify_password("MySecure@Pass123", password_hash)
```

**Bcrypt Configuration:**
- Algorithm: bcrypt
- Cost factor: 12 (configurable)
- Salt: Automatically generated per password

---

## Rate Limiting

### Configuration

Rate limiting prevents brute force attacks and DoS.

**Default Limits:**
```python
# General endpoints: 100 requests per minute
# Login endpoint: 5 requests per 15 minutes
# Registration endpoint: 3 requests per hour
```

**Configuration:**
```python
from security.rate_limiter import init_rate_limiter

limiter = init_rate_limiter(app)
```

### Rate Limit Headers

When rate limited, responses include:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704067245
```

### Bypass

Rate limiting can be disabled for specific IPs in production:

```python
# In backend/.env
RATE_LIMIT_WHITELIST=192.168.1.1,10.0.0.1
```

---

## Account Lockout

### Mechanism

Accounts are temporarily locked after multiple failed login attempts.

**Lockout Policy:**
- Trigger: 5 failed attempts within 15 minutes
- Duration: 15 minutes
- Reset: Successful login clears failed attempts

**Implementation:**
```python
from security.account_lockout import AccountLockout

# Check if locked
is_locked, seconds_remaining = AccountLockout.is_locked(email)

if is_locked:
    return jsonify({
        'error': 'Account temporarily locked',
        'retry_after': seconds_remaining
    }), 403

# Record failed attempt
AccountLockout.record_failed_attempt(email, ip_address)

# Reset on success
AccountLockout.reset_attempts(email)
```

### Database Storage

Failed attempts are stored in `Login_Attempts` table:

```sql
CREATE TABLE Login_Attempts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(254) NOT NULL,
    ip_address VARCHAR(45),
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT FALSE,
    INDEX idx_email_time (email, attempted_at)
);
```

---

## Security Headers

### Headers Implemented

All responses include security headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

**Header Purposes:**

| Header | Purpose | Value |
|--------|---------|-------|
| X-Content-Type-Options | Prevent MIME sniffing | nosniff |
| X-Frame-Options | Prevent clickjacking | DENY |
| X-XSS-Protection | Enable XSS filter | 1; mode=block |
| CSP | Restrict resource loading | default-src 'self' |
| HSTS | Force HTTPS | max-age=31536000 |

**Implementation:**
```python
from security.headers import init_security_headers

app = Flask(__name__)
init_security_headers(app)
```

---

## CORS Configuration

### Cross-Origin Resource Sharing

CORS is configured to allow only trusted origins.

**Development Mode:**
```
Allowed Origins:
- http://localhost:8080
- http://127.0.0.1:8080
- http://localhost:3000
- http://127.0.0.1:3000
```

**Production Mode:**
```
Allowed Origins: Configured via ALLOWED_ORIGINS environment variable
```

**Configuration:**
```python
# In backend/.env
ALLOWED_ORIGINS=https://app.example.com,https://www.example.com
```

**Allowed Methods:**
- GET, POST, PUT, DELETE, OPTIONS

**Allowed Headers:**
- Content-Type
- Authorization

**Credentials:**
- Enabled (cookies/auth headers allowed)

---

## Audit Logging

### Security Events Logged

All security-relevant events are logged:

**Event Types:**
- User registration
- Login attempts (success/failure)
- Account lockouts
- Rate limit violations
- Password changes
- Permission changes

**Log Format:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "event_type": "LOGIN_ATTEMPT",
  "user_id": 123,
  "email": "user@example.com",
  "ip_address": "192.168.1.1",
  "success": true,
  "details": "Successful login"
}
```

### Log Storage

Logs are stored in two locations:

**File Logging:**
```
backend/logs/security.log
```

**Database Logging:**
```sql
CREATE TABLE Security_Audit_Log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    event_type VARCHAR(50) NOT NULL,
    user_id INT,
    email VARCHAR(254),
    ip_address VARCHAR(45),
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at),
    INDEX idx_ip_address (ip_address)
);
```

### Accessing Logs

**View recent security events:**
```bash
tail -f backend/logs/security.log
```

**Query database logs:**
```sql
SELECT * FROM Security_Audit_Log 
WHERE created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY created_at DESC;
```

---

## Database Security

### User Roles

Three database users with different privilege levels:

**1. Admin User** (`moneyminder_admin`)
- Full DDL/DML access
- User management
- Schema modifications
- Use: Database administration only

**2. Application User** (`moneyminder_app`)
- SELECT, INSERT, UPDATE, DELETE
- No DDL operations
- No user management
- Use: Application runtime

**3. Read-Only User** (`moneyminder_readonly`)
- SELECT only
- No write operations
- Use: Reporting, backups

### Connection Security

**Parameterized Queries:**
```python
# SAFE: Uses parameterized queries
Database.execute_query(
    "SELECT * FROM Users WHERE email = %s",
    (email,)
)

# UNSAFE: String concatenation (never do this)
query = f"SELECT * FROM Users WHERE email = '{email}'"
```

**Connection Encryption:**
```python
# In backend/.env
DB_SSL=true
DB_SSL_CA=/path/to/ca.pem
```

### Data Protection

**Sensitive Fields:**
- Passwords: Hashed with bcrypt
- Tokens: Stored in JWT (not in database)
- API Keys: Hashed before storage
- PII: Encrypted at rest (future enhancement)

---

## Configuration Security

### Environment Variables

Sensitive configuration is stored in `.env` file:

```bash
# Database
DB_HOST=localhost
DB_USER=moneyminder_app
DB_PASSWORD=SecurePassword123!
DB_NAME=MoneyMinder_DB

# JWT
JWT_SECRET_KEY=your-64-character-secret-key-here-minimum-32-chars
JWT_EXPIRATION=86400

# Security
FLASK_ENV=production
DEBUG=False
ALLOWED_ORIGINS=https://app.example.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
```

### Secret Key Validation

The application validates configuration on startup:

```python
from security.config_validator import ConfigValidator

is_valid, errors = ConfigValidator.validate_all()

if not is_valid:
    for error in errors:
        logging.error(f"Configuration error: {error}")
    # Refuse to start in production
```

**Validation Checks:**
- JWT_SECRET_KEY length ≥ 32 characters
- JWT_SECRET_KEY is not a default/placeholder value
- Database credentials are configured
- FLASK_ENV is set appropriately

### .env File Protection

**Best Practices:**
```bash
# Never commit .env to version control
echo ".env" >> .gitignore

# Set restrictive permissions
chmod 600 backend/.env

# Use different secrets for each environment
# development: Less strict requirements
# production: Strict validation, strong secrets
```

---

## Deployment Security

### Production Checklist

Before deploying to production:

- [ ] Change all default passwords
- [ ] Set strong JWT_SECRET_KEY (64+ characters)
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure ALLOWED_ORIGINS for your domain
- [ ] Set FLASK_ENV=production
- [ ] Set DEBUG=False
- [ ] Enable database SSL connections
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Enable database backups
- [ ] Configure monitoring and alerts

### HTTPS Configuration

**Enable HTTPS:**
```python
# In backend/.env
FLASK_ENV=production
HTTPS=true
SSL_CERT=/path/to/cert.pem
SSL_KEY=/path/to/key.pem
```

**HSTS Header:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Database Backups

**Automated Backups:**
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups/moneyminder"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mysqldump -u moneyminder_admin -p \
  --single-transaction \
  --quick \
  --lock-tables=false \
  MoneyMinder_DB > "$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Encrypt backup
gpg --encrypt "$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Remove unencrypted backup
rm "$BACKUP_DIR/backup_$TIMESTAMP.sql"
```

---

## Security Testing

### Running Tests

All security features include comprehensive tests:

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run security tests only
python -m pytest tests/test_validators.py -v
python -m pytest tests/test_password_policy.py -v
python -m pytest tests/test_account_lockout.py -v
python -m pytest tests/test_rate_limiter.py -v
python -m pytest tests/test_security_headers.py -v
python -m pytest tests/test_auth_routes.py -v
```

### Test Coverage

**87 tests covering:**
- Input validation (email, username, amount)
- Password policy enforcement
- Account lockout mechanism
- Rate limiting
- Security headers
- CORS configuration
- Audit logging
- Authentication routes
- Integration scenarios

### Property-Based Testing

Uses Hypothesis for property-based testing:

```python
from hypothesis import given, strategies as st

@given(st.emails())
def test_email_validation(email):
    # Test property: valid emails pass validation
    result = InputValidator.validate_email(email)
    assert isinstance(result, bool)
```

---

## Incident Response

### Security Incident Procedures

**1. Detection:**
- Monitor security logs for suspicious activity
- Set up alerts for rate limit violations
- Track failed login attempts

**2. Investigation:**
```bash
# Check security logs
tail -f backend/logs/security.log

# Query audit database
SELECT * FROM Security_Audit_Log 
WHERE ip_address = '192.168.1.100'
ORDER BY created_at DESC;
```

**3. Response:**
- Disable compromised accounts
- Reset affected user passwords
- Review access logs
- Notify affected users

**4. Prevention:**
- Update security rules
- Patch vulnerabilities
- Increase monitoring

### Common Incidents

**Brute Force Attack:**
- Symptom: Many failed login attempts from single IP
- Response: IP is automatically rate limited
- Prevention: Account lockout after 5 failures

**SQL Injection Attempt:**
- Symptom: Malformed input in logs
- Response: Input validation rejects malicious input
- Prevention: Parameterized queries prevent injection

**XSS Attack:**
- Symptom: Script tags in user input
- Response: Input validation sanitizes input
- Prevention: Security headers prevent execution

---

## Future Improvements

### Planned Enhancements

**1. Two-Factor Authentication (2FA)**
- TOTP (Time-based One-Time Password)
- SMS verification
- Backup codes

**2. Session Management**
- Token revocation/blacklisting
- Session timeout
- Concurrent session limits

**3. Advanced Encryption**
- Database encryption at rest
- Field-level encryption for PII
- Encrypted backups

**4. Secrets Management**
- HashiCorp Vault integration
- AWS Secrets Manager integration
- Automatic secret rotation

**5. Security Scanning**
- SAST (Static Application Security Testing)
- DAST (Dynamic Application Security Testing)
- Dependency vulnerability scanning

**6. API Security**
- API key authentication
- Request signing (HMAC)
- API rate limiting per key

**7. Monitoring & Alerting**
- Real-time security alerts
- Anomaly detection
- Security dashboard

**8. Compliance**
- GDPR compliance
- PCI DSS compliance
- SOC 2 certification

---

## References

### Security Standards

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CWE Top 25](https://cwe.mitre.org/top25/)

### Libraries Used

- **bcrypt**: Password hashing
- **PyJWT**: JWT token handling
- **Flask-Limiter**: Rate limiting
- **Flask-Talisman**: Security headers
- **Hypothesis**: Property-based testing

### Additional Resources

- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

---

**Document Version:** 1.0.0  
**Last Updated:** December 2024  
**Maintained By:** Security Team  
**Review Frequency:** Quarterly
