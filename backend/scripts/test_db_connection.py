#!/usr/bin/env python
"""
Script to test PostgreSQL database connection for Educational Platform.
Author: nanthiniSanthanam
Date: 2025-04-21
"""

from django.db.utils import OperationalError
from django.db import connections
import os
import sys
import django
import time

# Add the project path to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educore.settings')
django.setup()

# Now you can import Django modules


def test_connection():
    """Test connection to the PostgreSQL database."""
    print("Testing connection to PostgreSQL database...")

    try:
        # Attempt to get a cursor
        db_conn = connections['default']
        db_conn.cursor()

        # Run a simple query
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            row = cursor.fetchone()
            print(f"Connection successful!")
            print(f"PostgreSQL version: {row[0]}")

        # Test connection to each model
        from django.apps import apps
        from django.db import connection

        print("\nTesting access to models:")
        for model in apps.get_models():
            model_name = f"{model._meta.app_label}.{model._meta.object_name}"
            try:
                # Just count the records to test access
                count = model.objects.count()
                print(f"✓ {model_name}: {count} records")
            except Exception as e:
                print(f"✗ {model_name}: Error - {str(e)}")

        return True

    except OperationalError as e:
        print(f"Connection failed: {e}")
        return False


if __name__ == "__main__":
    max_attempts = 3
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        if test_connection():
            sys.exit(0)
        elif attempt < max_attempts:
            wait_time = 2 ** attempt  # Exponential backoff
            print(
                f"Retrying in {wait_time} seconds... (Attempt {attempt}/{max_attempts})")
            time.sleep(wait_time)

    print("Failed to connect to the database after multiple attempts.")
    sys.exit(1)
