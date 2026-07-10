import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import base.river_urls  # we'll keep websocket routes next to normal urls

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gumsup4.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(base.urls.websocket_urlpatterns)
    ),
})
