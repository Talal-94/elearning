from django.urls import path
from .views import (
    course_list,
    course_detail,
    course_create,
    enroll_in_course,
    material_upload,
    give_feedback,
    post_status,
)

urlpatterns = [
    # Browsing
    path("courses/", course_list, name="course_list"),
    path("courses/<int:course_id>/", course_detail, name="course_detail"),

    # Teacher actions
    path("create/", course_create, name="course_create"),
    path("courses/<int:course_id>/materials/upload/", material_upload, name="material_upload"),

    # Student actions
    path("courses/<int:course_id>/enroll/", enroll_in_course, name="enroll"),
    path("courses/<int:course_id>/feedback/", give_feedback, name="give_feedback"),

    # Status updates (any user)
    path("status/", post_status, name="post_status"),
]
