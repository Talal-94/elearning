# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError  # <-- add this

class User(AbstractUser):
    STUDENT = 'student'
    TEACHER = 'teacher'
    ROLE_CHOICES = [(STUDENT, 'Student'), (TEACHER, 'Teacher')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)

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

