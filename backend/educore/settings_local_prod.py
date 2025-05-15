"""
settings_local_prod.py
--------------------------------------------------
Production-like settings for LOCAL simulation.
Imports base settings, tightens security, but
still works on 127.0.0.1 without TLS if needed.
"""

# fmt: off
# isort: skip_file

import os
from pathlib import Path
from datetime import timedelta
from .settings import *          # BASE settings already define BASE_DIR, etc.

# ---------------------------------------------------------------------------
# 0.  GENERAL
# ---------------------------------------------------------------------------
DEBUG = False

# Allow both your public domain AND localhost while developing HTTPS locally
ALLOWED_HOSTS = [
    'yourdomain.com',
    'www.yourdomain.com',
    'localhost',
    '127.0.0.1',
]

# ---------------------------------------------------------------------------
# 1.  SECURITY
# ---------------------------------------------------------------------------
# Toggle SSL redirect locally via ENV; default True in CI / cloud
SECURE_SSL_REDIRECT      = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SECURE_HSTS_SECONDS      = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD      = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER   = True
SESSION_COOKIE_SECURE       = SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE          = SECURE_SSL_REDIRECT
X_FRAME_OPTIONS             = 'DENY'

# ---------------------------------------------------------------------------
# 2.  DATABASE
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.postgresql',
        'NAME'    : os.getenv('DB_NAME', 'eduplatform_prod'),
        'USER'    : os.getenv('DB_USER', 'eduplatform'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST'    : os.getenv('DB_HOST', 'localhost'),
        'PORT'    : os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
    }
}

# ---------------------------------------------------------------------------
# 3.  STATIC / MEDIA
# ---------------------------------------------------------------------------
# For real prod deploy you’d push to CDN; locally we fall back to /static/
STATIC_URL = os.getenv('STATIC_URL', '/static/')
MEDIA_URL  = os.getenv('MEDIA_URL',  '/media/')

# ---------------------------------------------------------------------------
# 4.  JWT  /  AUTH
# ---------------------------------------------------------------------------
if 'rest_framework_simplejwt.token_blacklist' not in INSTALLED_APPS:
    INSTALLED_APPS.append('rest_framework_simplejwt.token_blacklist')

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME' : timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS' : True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN'     : True,
    'ALGORITHM'             : 'HS256',
    'SIGNING_KEY'           : SECRET_KEY,
    'AUTH_HEADER_TYPES'     : ('Bearer',),
    'USER_ID_FIELD'         : 'id',
    'USER_ID_CLAIM'         : 'user_id',
    'AUTH_TOKEN_CLASSES'    : ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM'      : 'token_type',
}

# ---------------------------------------------------------------------------
# 5.  LOGGING
# ---------------------------------------------------------------------------
# Create a portable logs directory *inside* the project
BASE_LOG_DIR = Path(BASE_DIR, 'logs')
BASE_LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version'               : 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {process:d} {thread:d} {message}',
            'style' : '{',
        },
    },
    'handlers': {
        'file': {
            'level'    : 'WARNING',
            'class'    : 'logging.handlers.RotatingFileHandler',
            'filename' : str(BASE_LOG_DIR / 'error.log'),
            'maxBytes' : 5_000_000,   # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'class'    : 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers' : ['file', 'console'],
            'level'    : 'WARNING',
            'propagate': True,
        },
    },
}
