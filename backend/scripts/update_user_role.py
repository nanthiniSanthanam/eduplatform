# fmt: off
# isort: skip_file
# 
# Script to update a user's role in the database
# Date: 2025-05-09

import os
import sys
import django

# Set up Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educore.settings_local')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

def update_user_role(email, new_role):
    """Update a user's role by email"""
    try:
        user = User.objects.get(email=email)
        old_role = user.role
        user.role = new_role
        user.save()
        print(f"User {email} role updated from '{old_role}' to '{new_role}'")
        return True
    except User.DoesNotExist:
        print(f"User with email {email} not found")
        return False
    except Exception as e:
        print(f"Error updating user role: {e}")
        return False

def list_users():
    """List all users and their roles"""
    users = User.objects.all().order_by('email')
    print(f"\nTotal users: {users.count()}")
    print("\nEmail                      | Role        | Is Verified")
    print("-" * 60)
    for user in users:
        print(f"{user.email[:25]:<25} | {user.role or 'None':<11} | {user.is_email_verified}")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments, just list users
        list_users()
    elif len(sys.argv) == 3:
        # Update user role
        email = sys.argv[1]
        new_role = sys.argv[2]
        if new_role not in ['student', 'instructor', 'admin']:
            print(f"Invalid role '{new_role}'. Must be 'student', 'instructor', or 'admin'")
            sys.exit(1)
        update_user_role(email, new_role)
    else:
        print("Usage:")
        print("  python update_user_role.py                       # List all users")
        print("  python update_user_role.py <email> <role>        # Update user role")
        print("  Roles: student, instructor, admin") 