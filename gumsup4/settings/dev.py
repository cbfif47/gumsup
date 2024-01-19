"""Settings for development."""


from .base import *
import os

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv("GOOGLE_CLIENT_ID", ""),
            'secret': os.getenv("GOOGLE_SECRET", ""),
            'key': ''
        },
        'SCOPE': [
            'email','profile',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
