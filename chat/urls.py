from django.urls import path
from .views import room_view

urlpatterns = [
    path('chat/<str:room_name>/', room_view, name='chat_room'),
]
