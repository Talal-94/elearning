import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils.encoding import force_str
from channels.db import database_sync_to_async

from courses.models import Course
from .permissions import can_access_course_chat


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Resolve course_id from kwarg (supports room_name fallback)
        kwargs = self.scope.get("url_route", {}).get("kwargs", {})
        course_id = kwargs.get("course_id")
        if course_id is None:
            room_name = kwargs.get("room_name")
            try:
                course_id = int(room_name)
            except (TypeError, ValueError):
                await self.close()
                return

        # Load course + check access
        try:
            course = await sync_to_async(
                Course.objects.select_related("instructor").get
            )(pk=course_id)
        except Course.DoesNotExist:
            await self.close()
            return

        user = self.scope.get("user")
        allowed = await sync_to_async(can_access_course_chat)(user, course)
        if not allowed:
            await self.close()
            return

        # Keep references for later
        self.course = course
        self.instructor_id = course.instructor_id
        self.room_group_name = f"course_{course.id}"

        # Join group and accept connection
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        """
        Accepts JSON payloads like {"message": "..."} (or "text"),
        and plain text / bytes as a fallback.
        Persists each message and broadcasts it with role + user_id.
        """
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
        user_id = getattr(user, "id", None)
        username = getattr(user, "username", "unknown")
        is_instructor = (user_id == self.instructor_id)

        # 1) Persist to DB
        await self._save_message(self.course.id, user_id, msg)

        # 2) Broadcast to the group with role + user_id
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": msg,
                "user": username,
                "user_id": user_id,
                "is_instructor": is_instructor,
            },
        )

    async def chat_message(self, event):
        # Fan-out to this socket
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "user": event["user"],
                    "user_id": event.get("user_id"),
                    "is_instructor": event.get("is_instructor", False),
                }
            )
        )

    # ------- DB helper -------
    @database_sync_to_async
    def _save_message(self, course_id: int, user_id: int, content: str):
        from .models import ChatMessage
        return ChatMessage.objects.create(
            course_id=course_id, user_id=user_id, content=content
        )


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
