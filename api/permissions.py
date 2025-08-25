from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model

User = get_user_model()

class IsTeacher(BasePermission):
    """Allow only teacher users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "role", None) == User.TEACHER)

class IsInstructorOwnerOrReadOnly(BasePermission):
    """
    Allow edits only if requester is the instructor/owner.
    Works for objects with `instructor` or `course.instructor`.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        instructor = getattr(obj, "instructor", None)
        if instructor is None and hasattr(obj, "course"):
            instructor = getattr(obj.course, "instructor", None)
        return bool(instructor and request.user and getattr(instructor, "id", None) == request.user.id)
