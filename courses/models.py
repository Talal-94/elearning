from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Course(models.Model):
    title       = models.CharField(max_length=200)
    description = models.TextField()
    instructor  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Enrollment(models.Model):
    student     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course      = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} → {self.course}"

class Material(models.Model):
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title      = models.CharField(max_length=200)
    upload     = models.FileField(upload_to='course_materials/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.course})"

class Feedback(models.Model):
    student    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='feedbacks')
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.student} on {self.course}"

class StatusUpdate(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='status_updates')
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}: {self.content[:30]}…"
