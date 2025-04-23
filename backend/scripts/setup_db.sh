#!/bin/bash

# Setup script for PostgreSQL database for Educational Platform
# Author: nanthiniSanthanam
# Date: 2025-04-21

echo "Setting up PostgreSQL for Educational Platform..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null
then
    echo "PostgreSQL is not installed. Please install PostgreSQL first."
    exit 1
fi

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo ".env file not found. Creating from template..."
    cp ../.env.example ../.env
    echo "Please update the .env file with your database credentials."
fi

# Source .env file
source ../.env

# Create database and user
echo "Creating database and user..."
sudo -u postgres psql << EOF
-- Create database if not exists
CREATE DATABASE $DB_NAME;

-- Create user if not exists
DO
\$do\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE rolname = '$DB_USER') THEN
      CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
   END IF;
END
\$do\$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Connect to database
\c $DB_NAME

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOF

echo "Database setup complete."

# Migrate Django models
echo "Running migrations..."
cd ..
python manage.py migrate

echo "Creating admin user..."
python manage.py createsuperuser --username admin --email admin@example.com

echo "Setup complete!"