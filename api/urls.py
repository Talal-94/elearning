from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    EnrollmentViewSet,
    MaterialViewSet,
    FeedbackViewSet,
)

router = DefaultRouter()
router.register(r'courses',     CourseViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'materials',   MaterialViewSet)
router.register(r'feedbacks',   FeedbackViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
