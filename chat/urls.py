from django.urls import path
from .views import room

urlpatterns = [
    path("chat/<int:course_id>/", room, name="chat_room"),
]
