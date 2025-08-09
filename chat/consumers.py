import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from courses.models import Course, Enrollment


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Per-course chat.
    Authorization rule (defense in depth):
      - allow if user is authenticated AND (course.instructor == user OR user is enrolled)
      - otherwise reject the socket.
    """

    async def connect(self):
        user = self.scope.get("user", AnonymousUser())
        # URL kwarg from routing: path("ws/chat/<room_name>/", ...)
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]

        # validate course id
        try:
            self.course_id = int(self.room_name)
        except (TypeError, ValueError):
            await self.close()
            return

        # fetch course
        course = await self._get_course(self.course_id)
        if not course or not user.is_authenticated:
            await self.close()
            return

        allowed = await self._is_allowed(user.id, self.course_id, course.instructor_id)
        if not allowed:
            await self.close()
            return

        self.room_group_name = f"chat_{self.course_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # leave room
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message = (data.get("message") or "").strip()
        if not message:
            return

        user = self.scope.get("user")
        username = getattr(user, "username", "unknown")

        # broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "message": message, "user": username},
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"message": event["message"], "user": event["user"]}))

    # ------- DB helpers -------
    @database_sync_to_async
    def _get_course(self, course_id: int):
        try:
            return Course.objects.only("id", "instructor_id").get(pk=course_id)
        except Course.DoesNotExist:
            return None

    @database_sync_to_async
    def _is_allowed(self, user_id: int, course_id: int, instructor_id: int) -> bool:
        if user_id == instructor_id:
            return True
        return Enrollment.objects.filter(course_id=course_id, student_id=user_id).exists()
