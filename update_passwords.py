#!/usr/bin/env python3
"""
Script to generate bcrypt hashed passwords for sample data
Run this to update the Sample_Data.sql file with properly hashed passwords
"""

import bcrypt

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Generate bcrypt hash for the demo password
demo_password = "Demo@2024"
bcrypt_hash = hash_password(demo_password)

print("=" * 60)
print("PASSWORD HASH GENERATOR FOR SAMPLE DATA")
print("=" * 60)
print(f"\nOriginal Password: {demo_password}")
print(f"Bcrypt Hash: {bcrypt_hash}")
print("\nUpdate Sample_Data.sql with this hash:")
print("-" * 60)
print("\nReplace the INSERT INTO Users statement with:\n")
print("""INSERT INTO Users (username, email, password_hash, base_currency, created_at) VALUES 
('john_doe', 'john.doe@example.com', '%s', 'VND', '2024-01-15 10:00:00'),
('jane_smith', 'jane.smith@example.com', '%s', 'USD', '2024-02-20 14:30:00'),
('nguyen_van_a', 'nguyenvana@example.com', '%s', 'VND', '2024-03-10 09:15:00'),
('tran_thi_b', 'tranthib@example.com', '%s', 'VND', '2024-03-12 11:20:00');""" % (bcrypt_hash, bcrypt_hash, bcrypt_hash, bcrypt_hash))

print("\n" + "=" * 60)
print("NOTE: All demo users will have the same password: Demo@2024")
print("=" * 60)
