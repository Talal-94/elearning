from django.urls import path
from .consumers import ChatConsumer, NotificationsConsumer

websocket_urlpatterns = [
    path("ws/chat/<int:course_id>/", ChatConsumer.as_asgi()),
    path("ws/notifications/", NotificationsConsumer.as_asgi()),
]
