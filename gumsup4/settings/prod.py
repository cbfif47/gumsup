"""Settings for production."""


from .base import *


DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = ['.rexwithfriends.com',
    "thisismansions.com",
    "www.thisismansions.com",
    "chris-browder.com",
    "www.chris-browder.com",]


RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

ADMINS = []

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")]},
    }
}

PUSH_NOTIFICATIONS_SETTINGS = {
    "APNS_AUTH_KEY_PATH": os.getenv("APNS_AUTH_KEY_PATH"),
    "APNS_AUTH_KEY_ID": os.getenv("APNS_AUTH_KEY_ID"),
    "APNS_TEAM_ID": os.getenv("APNS_TEAM_ID"),
    "APNS_TOPIC": "rexwithfriends.Rex-With-Friends",
    "APNS_USE_ALTERNATIVE_PORT": 2197,
    "APNS_USE_SANDBOX": os.getenv("APNS_USE_SANDBOX", "True") == "True",
}

DAYCARE_API_TOKEN = os.environ['DAYCARE_API_TOKEN']