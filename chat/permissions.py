from django.contrib.auth import get_user_model
from accounts.models import Block
from courses.models import Enrollment

User = get_user_model()

def can_access_course_chat(user, course) -> bool:
    # only instructor of the course or enrolled students.
    if not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "role", None) == User.TEACHER and course.instructor_id == user.id:
        return True

    # Blocked students are denied, even if enrolled.
    if getattr(user, "role", None) == User.STUDENT:
        if Block.objects.filter(teacher=course.instructor, blocked=user).exists():
            return False
        return Enrollment.objects.filter(course=course, student=user).exists()

    return False
