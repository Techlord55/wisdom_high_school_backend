# Location: .\config\settings\dev.py

# ==================== config/settings/dev.py ====================
from .base import *

# Force DEBUG to True in development - don't read from env again
if not DEBUG:
    DEBUG = True

# Ensure ALLOWED_HOSTS is set for development
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# Development-specific apps
INSTALLED_APPS += [
    'django_extensions',
]

# CORS - Allow all in development
CORS_ALLOW_ALL_ORIGINS = True


# Logging
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
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
