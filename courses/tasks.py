from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Course, Enrollment, Material, Feedback
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def notify_new_enrollment(enrollment_id):
    enrollment = Enrollment.objects.select_related('student','course__instructor').get(pk=enrollment_id)
    instructor = enrollment.course.instructor
    student = enrollment.student
    send_mail(
        subject=f"New enrollment in {enrollment.course.title}",
        message=f"{student.username} has enrolled in your course “{enrollment.course.title}.”",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[instructor.email],
    )

@shared_task
def notify_new_material(material_id):
    material = Material.objects.select_related('course').get(pk=material_id)
    students = material.course.enrollments.select_related('student').all()
    emails = [en.student.email for en in students]
    send_mail(
        subject=f"New material in {material.course.title}",
        message=f"“{material.title}” was uploaded to {material.course.title}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=emails,
    )

@shared_task
def notify_new_feedback(feedback_id):
    feedback = Feedback.objects.select_related('student','course__instructor','course').get(pk=feedback_id)
    instructor = feedback.course.instructor
    send_mail(
        subject=f"New feedback on {feedback.course.title}",
        message=f"{feedback.student.username} left feedback: “{feedback.content[:100]}…”",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[instructor.email],
    )
