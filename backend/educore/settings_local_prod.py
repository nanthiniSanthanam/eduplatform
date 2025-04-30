r"""
File: C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\backend\educore\settings_local_prod.py
Purpose: Production-like settings that run on your local machine

This file configures Django to simulate production settings while still
running on your local computer. This gives you a way to test everything
works as expected before deploying to a real hosting provider.

Variables you might need to modify:
- SECRET_KEY: For local testing, this doesn't need to be changed
- ALLOWED_HOSTS: Add your local machine name if needed
- DATABASE settings: Update if you want to use a dedicated database
"""
import os
from .db_settings import *
from .settings import *

# Turn off debug mode to simulate production
DEBUG = False

# But allow showing detailed errors for testing purposes
SHOW_DETAILED_ERRORS = True

# Allow connections from localhost
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Keep the database settings from your development environment

# Use the file system for email sending instead of actually sending emails
# This will save emails as files you can inspect in a folder
# MAIL_BACKEND = 'django.core.mail.backends.filebacked.EmailBackend'
# EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'sent_emails')

# Frontend URL for email links
FRONTEND_URL = 'http://localhost:3000'

# Make media and static files work locally
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static_collected')


# Email Configuration for Production
# Add this section to your settings.py file

# Use SMTP backend for actually sending emails
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# SMTP Server Configuration
# For Gmail
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# For Outlook/Office 365, use:
# EMAIL_HOST = 'smtp.office365.com'
# For custom domain, use your hosting provider's SMTP settings

# Authentication
EMAIL_HOST_USER = 'nanthini.santhanam@gmail.com'  # Your actual Gmail address
# (For better security, use environment variables instead of hardcoding)
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# Sender email address (displayed in From: field)
DEFAULT_FROM_EMAIL = 'EduPlatform <nanthini.santhanam@gmail.com>'
# Optional: separate address for error notifications
SERVER_EMAIL = 'nanthini.santhanam@gmail.com'

# Timeout settings
EMAIL_TIMEOUT = 30  # seconds before connection times out

# For production, consider rate limiting to prevent abuse
# This requires additional configuration with a rate limiting library


# Ensure we can see errors in the local production environment
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
