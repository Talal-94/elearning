from django.urls import re_path, path
from .consumers import ChatConsumer
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),
    path("ws/notifications/", consumers.NotificationsConsumer.as_asgi()), 

]
