"""Settings for development."""


from .base import *
import os

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv("GOOGLE_CLIENT_ID", "783167709776-15e461nams47q30csnpi7m93tqvmvekn.apps.googleusercontent.com"),
            'secret': os.getenv("GOOGLE_SECRET", "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"),
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
