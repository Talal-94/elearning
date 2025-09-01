from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (
    UserSerializer, CourseSerializer, EnrollmentSerializer,
    MaterialSerializer, FeedbackSerializer,
)
from .permissions import IsTeacher, IsInstructorOwnerOrReadOnly
from courses.models import Course, Enrollment, Material, Feedback

User = get_user_model()

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        return Response(self.get_serializer(request.user).data)

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.select_related("instructor").all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsTeacher(), IsInstructorOwnerOrReadOnly()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        if getattr(self.request.user, "role", None) != User.TEACHER:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only teachers can create courses.")
        serializer.save(instructor=self.request.user)

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.select_related("student", "course").all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        return qs.filter(course__instructor=u) if getattr(u, "role", None) == User.TEACHER else qs.filter(student=u)

class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.select_related("course__instructor").all()
    serializer_class = MaterialSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsTeacher(), IsInstructorOwnerOrReadOnly()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        course = serializer.validated_data.get("course")
        if not course or course.instructor_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only the course instructor can add materials.")
        serializer.save()

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.select_related("student", "course__instructor").all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        return qs.filter(course__instructor=u) if getattr(u, "role", None) == User.TEACHER else qs.filter(student=u)

    def perform_create(self, serializer):
        u = self.request.user
        if getattr(u, "role", None) == User.TEACHER:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only students can post feedback.")
        course = serializer.validated_data.get("course")
        if not course:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"course": "This field is required."})
        is_enrolled = Enrollment.objects.filter(course=course, student=u).exists()
        if not is_enrolled:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Enroll in the course first to post feedback.")
        serializer.save(student=u)
