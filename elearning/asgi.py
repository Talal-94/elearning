# elearning/asgi.py
import os
import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "elearning.settings")

# Initialize Django BEFORE importing anything that touches models
django.setup()

# Build the HTTP app first (this also ensures apps are ready)
django_asgi_app = get_asgi_application()

# Now it's safe to import routing/consumers that import models
import chat.routing  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})
