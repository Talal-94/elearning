import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils.encoding import force_str
from django.utils import timezone
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from courses.models import Course
from .permissions import can_access_course_chat

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        kwargs = self.scope.get("url_route", {}).get("kwargs", {})
        course_id = kwargs.get("course_id") or kwargs.get("room_name")

        try:
            self.course_id = int(course_id)
        except (TypeError, ValueError):
            await self.close()
            return

        try:
            self.course = await sync_to_async(
                Course.objects.select_related("instructor").get
            )(pk=self.course_id)
        except Course.DoesNotExist:
            await self.close()
            return

        user = self.scope.get("user")
        allowed = await sync_to_async(can_access_course_chat)(user, self.course)
        if not allowed:
            await self.close()
            return

        self.room_group_name = f"course_{self.course.id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        msg = ""
        if text_data:
            try:
                data = json.loads(text_data)
                msg = (data.get("message") or data.get("text") or "").strip()
            except json.JSONDecodeError:
                msg = text_data.strip()
        elif bytes_data:
            msg = force_str(bytes_data).strip()

        if not msg:
            return

        user = self.scope.get("user")

        await self._save_message(self.course_id, user.id, msg)

        payload = {
            "type": "chat.message",
            "message": msg,
            "user": {
                "id": user.id,
                "username": getattr(user, "username", "unknown"),
                "is_instructor": (self.course.instructor_id == user.id),
            },
            "timestamp": timezone.now().isoformat(),
        }
        await self.channel_layer.group_send(self.room_group_name, payload)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "user": event["user"],
            "timestamp": event.get("timestamp"),
        }))

    @database_sync_to_async
    def _save_message(self, course_id: int, user_id: int, content: str):
        from .models import ChatMessage
        return ChatMessage.objects.create(course_id=course_id, user_id=user_id, content=content)


class NotificationsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return
        self.user_group = f"user_{user.id}"
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def notify(self, event):
        await self.send(text_data=json.dumps(event["payload"]))
