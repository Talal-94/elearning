import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from courses.models import Course, Enrollment

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.group_name = f"chat_{self.room_name}"

        user = self.scope.get("user")
        can_join = await self._can_join(user, self.room_name)
        if not can_join:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "").strip()
        if not message:
            return
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "chat_message", "message": message, "user": self.scope["user"].username},
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"message": event["message"], "user": event["user"]}))

    @database_sync_to_async
    def _can_join(self, user, course_id):
        if not user or not user.is_authenticated:
            return False
        try:
            course = Course.objects.select_related("instructor").get(pk=int(course_id))
        except (Course.DoesNotExist, ValueError, TypeError):
            return False
        if user == course.instructor:
            return True
        return Enrollment.objects.filter(course=course, student=user).exists()
