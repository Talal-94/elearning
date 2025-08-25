import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils.encoding import force_str
from courses.models import Course, Enrollment
from .permissions import can_access_course_chat

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        kwargs = self.scope.get("url_route", {}).get("kwargs", {})
        course_id = kwargs.get("course_id")
        if course_id is None:
            room_name = kwargs.get("room_name")
            try:
                course_id = int(room_name)
            except (TypeError, ValueError):
                await self.close()
                return

        try:
            course = await sync_to_async(Course.objects.select_related("instructor").get)(pk=course_id)
        except Course.DoesNotExist:
            await self.close()
            return

        user = self.scope.get("user")
        allowed = await sync_to_async(can_access_course_chat)(user, course)
        if not allowed:
            await self.close()
            return

        self.room_group_name = f"course_{course.id}"

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
        username = getattr(user, "username", "unknown")

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "message": msg, "user": username},
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"message": event["message"], "user": event["user"]}))
