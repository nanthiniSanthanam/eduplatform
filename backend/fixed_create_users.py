# fmt: off
# isort: skip_file

r"""
File: C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\backend\fixed_create_users.py

Purpose: Creates test users with different access levels for your educational platform.

This script:
1. Properly configures Django settings before importing any models
2. Creates three types of users for testing your educational platform:
   - Basic user (basic@example.com): Unregistered user who can view basic content
   - Intermediate user (intermediate@example.com): Registered user who can view intermediate content
   - Premium user (premium@example.com): Paid user who can view advanced content with certificates
3. Sets up appropriate subscription levels for each user

Variables to modify if needed:
- SCRIPT_DIR: The path to your backend directory (automatically set)
- TEST_USERS: The list of users to create, with details for each user:
  - email: User's email address
  - username: User's username
  - password: User's password
  - first_name: User's first name
  - last_name: User's last name
  - subscription: Settings for user's subscription level (tier, status)

Requirements:
- Python 3.8 or higher
- Django 3.2 or higher
- PostgreSQL database configured in settings.py

How to run this script:
1. Make sure your virtual environment is activated:
   venv\Scripts\activate
2. Run the script:
   python fixed_create_users.py
3. Check for success messages in the console

Created by: Professor Santhanam
Last updated: 2025-04-27 16:48:22
"""

#####################################################
# DJANGO CONFIGURATION SECTION
# Do not modify this section unless you know what you're doing
#####################################################

# Standard library imports - these come with Python

import django
import os
import sys
import traceback

# Get the absolute path to your project directory
# This helps Python find your project files
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
print(f"Project directory: {SCRIPT_DIR}")

# Add your project directory to the Python path
# This is required for Python to find your Django modules
sys.path.insert(0, SCRIPT_DIR)
print("Added project directory to Python path")

# Set the Django settings module environment variable
# This tells Django where to find your settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'educore.settings'
print("Set Django settings module to 'educore.settings'")

# Before importing any Django models, initialize Django
print("Initializing Django...")
django.setup()
print("Django initialized successfully!")


# Now it's safe to import Django models
print("Importing Django models...")
from django.contrib.auth import get_user_model
from users.models import Subscription
from django.utils import timezone
print("Models imported successfully!")

#####################################################
# USER DATA SECTION
# You can modify the user details below if needed
#####################################################

# Get the User model defined in your settings
User = get_user_model()

# Define test users for the three-tier system
TEST_USERS = [
    {
        'email': 'basic@example.com',
        'username': 'basic_user',
        'password': 'testpassword123',
        'first_name': 'Basic',
        'last_name': 'User',
        'is_email_verified': True,
        'role': 'student',
        'subscription': {
            'tier': 'free',
            'status': 'active'
        }
    },
    {
        'email': 'intermediate@example.com',
        'username': 'intermediate_user',
        'password': 'testpassword123',
        'first_name': 'Intermediate',
        'last_name': 'User',
        'is_email_verified': True,
        'role': 'student',
        'subscription': {
            'tier': 'basic',
            'status': 'active'
        }
    },
    {
        'email': 'premium@example.com',
        'username': 'premium_user',
        'password': 'testpassword123',
        'first_name': 'Premium',
        'last_name': 'User',
        'is_email_verified': True,
        'role': 'student',
        'subscription': {
            'tier': 'premium',
            'status': 'active'
        }
    }
]

#####################################################
# USER CREATION SECTION
# This section handles creating or updating users
#####################################################


def create_test_users():
    """Create or update test users with appropriate access levels."""
    print("\nCreating test users for your educational platform...\n")
    print("These users will allow you to test your three-tier access system:\n")
    print("1. Basic User: Unregistered user who can view basic content")
    print("2. Intermediate User: Registered user who can view intermediate content")
    print("3. Premium User: Paid user who can view advanced content with certificates\n")

    for user_data in TEST_USERS:
        # Extract subscription data from user data
        # We need to handle this separately from the user creation
        subscription_data = user_data.pop('subscription')

        try:
            # Check if user already exists
            if User.objects.filter(email=user_data['email']).exists():
                # Update existing user
                user = User.objects.get(email=user_data['email'])
                print(f"User {user_data['email']} already exists, updating...")

                # Update user fields (except password which requires special handling)
                password = user_data.pop('password', None)
                for key, value in user_data.items():
                    setattr(user, key, value)

                # Update password if provided
                if password:
                    user.set_password(password)

                user.save()
                print(f"Updated user: {user.email}")
            else:
                # Create new user with create_user method which handles password hashing
                user = User.objects.create_user(**user_data)
                print(f"Created new user: {user.email}")

            # Create or update subscription
            try:
                subscription = Subscription.objects.get(user=user)
                subscription.tier = subscription_data['tier']
                subscription.status = subscription_data['status']
                subscription.save()
                print(
                    f"Updated subscription for {user.email}: {subscription.tier}")
            except Subscription.DoesNotExist:
                # Create new subscription
                subscription = Subscription.objects.create(
                    user=user,
                    tier=subscription_data['tier'],
                    status=subscription_data['status'],
                    start_date=timezone.now()  # Set current time as start date
                )
                print(
                    f"Created subscription for {user.email}: {subscription.tier}")

        except Exception as e:
            print(
                f"Error creating/updating user {user_data['email']}: {str(e)}")
            traceback.print_exc()  # Print detailed error information

#####################################################
# MAIN SCRIPT EXECUTION
# This section runs when you execute the script
#####################################################


if __name__ == "__main__":
    try:
        print("-" * 80)
        print("EDUCATIONAL PLATFORM - TEST USER CREATION TOOL")
        print("-" * 80)
        create_test_users()
        print("\nTest users created successfully!")
        print("\nYou can now log in with these credentials:")
        print("1. Basic User: basic@example.com / testpassword123")
        print("2. Intermediate User: intermediate@example.com / testpassword123")
        print("3. Premium User: premium@example.com / testpassword123")
        print("-" * 80)
    except Exception as e:
        print("\n" + "!" * 80)
        print("ERROR CREATING TEST USERS")
        print("!" * 80)
        print(f"An error occurred: {str(e)}")
        print("\nDetailed error information:")
        traceback.print_exc()
        print("\nTROUBLESHOOTING TIPS:")
        print(
            "1. Check that your virtual environment is activated (venv\\Scripts\\activate)")
        print("2. Make sure all required packages are installed (pip install -r requirements.txt)")
        print("3. Verify that educore/settings.py exists and contains your database configuration")
        print("4. Make sure your database is running and accessible")
        print("5. Try running Django migrations first: python manage.py migrate")
        print("6. Check the exact error message above for more specific guidance")
        print("!" * 80)
