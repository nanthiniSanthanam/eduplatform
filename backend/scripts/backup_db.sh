#!/bin/bash

# Backup script for PostgreSQL database
# Author: nanthiniSanthanam
# Date: 2025-04-21

# Source .env file
source ../.env

# Create backup directory
BACKUP_DIR="../backups"
mkdir -p $BACKUP_DIR

# Create backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/eduplatform_backup_$TIMESTAMP.sql"

echo "Backing up database to $BACKUP_FILE..."

# Perform backup
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -F c -b -v -f $BACKUP_FILE $DB_NAME

echo "Backup completed successfully!"