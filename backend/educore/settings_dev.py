"""Development settings for Educational Platform."""

from .settings import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Use local database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'eduplatform'),
        'USER': os.environ.get('DB_USER', 'eduplatform_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'Vajjiram@79'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
