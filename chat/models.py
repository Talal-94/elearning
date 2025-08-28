from django.db import models
from django.conf import settings
from courses.models import Course


class ChatMessage(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="chat_messages"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_messages"
    )
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["course", "created_at"]),
        ]

    def __str__(self):
        uname = getattr(self.user, "username", self.user_id)
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {uname} → course {self.course_id}: {self.content[:40]}"
