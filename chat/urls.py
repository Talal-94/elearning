from django.urls import path
from . import views

urlpatterns = [
    path("chat/<int:course_id>/", views.room, name="chat_room"),
]
