#!/bin/bash
# ==========================================================
# Database Update Script for Bcrypt Password Migration
# ==========================================================
# This script updates existing sample data with bcrypt hashes
# Run this ONLY if you already have the old SHA256 passwords

echo "============================================================"
echo "MoneyMinder - Password Migration to Bcrypt"
echo "============================================================"
echo ""
echo "⚠️  WARNING: This will update all demo user passwords"
echo "   Old passwords (SHA256) will be replaced with bcrypt hashes"
echo ""
read -p "Do you want to continue? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Migration cancelled."
    exit 1
fi

echo ""
echo "Updating user passwords..."
echo ""

# Bcrypt hash for "Demo@2024"
BCRYPT_HASH='$2b$12$Uin1HqNfQFTLFSVrt6pEXeVJs22kEm78reC57/oeIrqn4XvE31wCu'

# Database credentials (update these if needed)
DB_NAME="MoneyMinder_DB"
DB_USER="moneyminder_admin"
DB_PASS="Admin@2024"  # Update this with your actual password

# Update each demo user
mysql -u $DB_USER -p$DB_PASS $DB_NAME << EOF
UPDATE Users 
SET password_hash = '$BCRYPT_HASH'
WHERE email IN (
    'john.doe@example.com',
    'jane.smith@example.com',
    'nguyenvana@example.com',
    'tranthib@example.com'
);

SELECT 
    username, 
    email, 
    SUBSTRING(password_hash, 1, 20) as 'Password Hash (preview)' 
FROM Users 
WHERE email IN (
    'john.doe@example.com',
    'jane.smith@example.com',
    'nguyenvana@example.com',
    'tranthib@example.com'
);
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Password migration completed successfully!"
    echo ""
    echo "Demo users updated:"
    echo "  - john.doe@example.com"
    echo "  - jane.smith@example.com"
    echo "  - nguyenvana@example.com"
    echo "  - tranthib@example.com"
    echo ""
    echo "All demo users still use password: Demo@2024"
    echo ""
else
    echo ""
    echo "❌ Migration failed. Check your database credentials."
    echo ""
    exit 1
fi

echo "============================================================"
echo "Next steps:"
echo "1. Restart your backend server if it's running"
echo "2. Test login with: john.doe@example.com / Demo@2024"
echo "3. All new registrations will automatically use bcrypt"
echo "============================================================"
