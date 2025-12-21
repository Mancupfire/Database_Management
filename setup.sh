#!/bin/bash

# MoneyMinder Setup Script
echo "=================================================="
echo "MoneyMinder - Setup & Installation"
echo "=================================================="

# Check if MySQL is installed
if ! command -v mysql &> /dev/null; then
    echo "❌ MySQL is not installed. Please install MySQL first."
    exit 1
fi

echo "✓ MySQL is installed"

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

echo "✓ Python3 is installed"

# Step 1: Database Setup
echo ""
echo "Step 1: Setting up database..."
echo "WARNING: This will DROP and recreate MoneyMinder_DB."
read -p "Continue? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi
echo "Please enter your MySQL root password when prompted:"

mysql -u root -p < Physical_Schema_Definition.sql
if [ $? -eq 0 ]; then
    echo "✓ Database schema created successfully"
else
    echo "❌ Failed to create database schema"
    exit 1
fi

mysql -u root -p < Sample_Data.sql
if [ $? -eq 0 ]; then
    echo "✓ Sample data inserted successfully"
else
    echo "❌ Failed to insert sample data"
    exit 1
fi

# Step 2: Backend Setup
echo ""
echo "Step 2: Setting up backend..."

cd backend

# Create virtual environment
python3 -m venv venv
if [ $? -eq 0 ]; then
    echo "✓ Virtual environment created"
else
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ Python dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ .env file created (please update with your settings)"
else
    echo "✓ .env file already exists"
fi

cd ..

echo ""
echo "=================================================="
echo "Setup completed successfully! 🎉"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Update backend/.env with your database credentials"
echo "2. Run: ./run.sh"
echo ""
