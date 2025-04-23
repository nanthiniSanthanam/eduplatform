#!/usr/bin/env python
"""
Verification script to check the educational platform setup.
"""

from django.db.utils import OperationalError
from django.contrib.auth import get_user_model
from django.apps import apps
from django.db import connection
import os
import sys
import django
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

# Add the project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educore.settings')
django.setup()

# Import Django models and apps

User = get_user_model()


def print_status(message, status, details=None):
    """Print a status message with color."""
    if status == "OK":
        status_color = Fore.GREEN + "✓ " + Style.RESET_ALL
    elif status == "WARNING":
        status_color = Fore.YELLOW + "! " + Style.RESET_ALL
    elif status == "ERROR":
        status_color = Fore.RED + "✗ " + Style.RESET_ALL
    else:
        status_color = status

    print(f"{status_color} {message}")

    if details:
        # Indent details
        detail_lines = details.split('\n')
        for line in detail_lines:
            print(f"    {line}")


def check_database_connection():
    """Check if the database connection works."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print_status("Database connection", "OK",
                         f"PostgreSQL version: {version}")
        return True
    except OperationalError as e:
        print_status("Database connection", "ERROR", f"Error: {e}")
        return False


def check_models():
    """Check if Django models exist and can be accessed."""
    try:
        models = apps.get_models()
        model_count = len(models)
        print_status("Django models", "OK", f"Found {model_count} models")

        # Try to access each model's objects
        for model in models:
            model_name = f"{model._meta.app_label}.{model._meta.object_name}"
            try:
                count = model.objects.count()
                print_status(f"Model {model_name}", "OK",
                             f"Record count: {count}")
            except Exception as e:
                print_status(f"Model {model_name}", "ERROR", f"Error: {e}")

        return True
    except Exception as e:
        print_status("Django models", "ERROR", f"Error: {e}")
        return False


def check_users():
    """Check if users can be created and accessed."""
    try:
        user_count = User.objects.count()
        print_status("User model", "OK", f"Found {user_count} users")

        # Check for a superuser
        superusers = User.objects.filter(is_superuser=True)
        if superusers.exists():
            print_status("Superuser", "OK",
                         f"Found {superusers.count()} superuser(s)")
        else:
            print_status("Superuser", "WARNING",
                         "No superuser found. Create one with: python manage.py createsuperuser")

        return True
    except Exception as e:
        print_status("User model", "ERROR", f"Error: {e}")
        return False


def check_table_structure():
    """Check the table structure in the database."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tablename FROM pg_catalog.pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """)
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            print_status("Database tables", "OK",
                         f"Found {len(tables)} tables: {', '.join(table_names)}")

            # Check for essential tables
            essential_tables = [
                'auth_user',
                'courses_course',
                'courses_module',
                'courses_lesson',
                'courses_enrollment'
            ]

            missing_tables = [
                table for table in essential_tables if table not in table_names]

            if missing_tables:
                print_status("Essential tables", "WARNING",
                             f"Missing tables: {', '.join(missing_tables)}")
            else:
                print_status("Essential tables", "OK",
                             "All essential tables exist")

        return True
    except Exception as e:
        print_status("Database tables", "ERROR", f"Error: {e}")
        return False


def main():
    """Run all verification checks."""
    print(Fore.CYAN + "\n=== EDUCATIONAL PLATFORM VERIFICATION ===" + Style.RESET_ALL)

    # Run checks
    db_ok = check_database_connection()

    if db_ok:
        table_ok = check_table_structure()
        models_ok = check_models()
        users_ok = check_users()

        # Summary
        print("\n" + Fore.CYAN + "=== VERIFICATION SUMMARY ===" + Style.RESET_ALL)

        all_ok = db_ok and table_ok and models_ok and users_ok

        if all_ok:
            print_status(
                "All checks passed! Your system is correctly set up.", "OK")
        else:
            print_status(
                "Some checks failed. Please review the issues above.", "WARNING")
    else:
        print("\n" + Fore.RED +
              "Database connection failed. Fix database issues before continuing." + Style.RESET_ALL)


if __name__ == "__main__":
    main()
