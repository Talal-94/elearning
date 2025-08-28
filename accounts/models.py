# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError 
from django.utils import timezone

class User(AbstractUser):
    STUDENT = 'student'
    TEACHER = 'teacher'
    ROLE_CHOICES = [(STUDENT, 'Student'), (TEACHER, 'Teacher')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    website_url = models.URLField(blank=True)
    expertise = models.CharField(max_length=200, blank=True)   
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    social_twitter = models.URLField(blank=True)
    social_linkedin = models.URLField(blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class Block(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocks_made')
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('teacher', 'blocked')

    def __str__(self):
        return f"{self.teacher.username} blocked {self.blocked.username}"

    def clean(self):
        if self.teacher_id == self.blocked_id:
            raise ValidationError("You cannot block yourself.")
        if getattr(self.teacher, "role", None) != User.TEACHER:
            raise ValidationError("Only teachers can block users.")
        if getattr(self.blocked, "role", None) != User.STUDENT:
            raise ValidationError("Only students can be blocked.")

    def save(self, *args, **kwargs):
        self.full_clean()  
        return super().save(*args, **kwargs)

class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="actions"
    )
    verb = models.CharField(max_length=140)
    url = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    def mark_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at"])

    def __str__(self):
        who = getattr(self.recipient, "username", "user")
        return f"To {who}: {self.verb}"
