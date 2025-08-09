from django.urls import path
from .views import (
    course_list,
    course_detail,
    course_create,
    enroll_in_course,
    unenroll_student,
    material_upload,
    give_feedback,
    post_status,
)

urlpatterns = [
    path("", course_list, name="course_list"),
    path("<int:course_id>/", course_detail, name="course_detail"),
    path("create/", course_create, name="course_create"),
    path("<int:course_id>/enroll/", enroll_in_course, name="enroll"),
    path("<int:course_id>/unenroll/<int:student_id>/", unenroll_student, name="unenroll_student"),
    path("<int:course_id>/materials/upload/", material_upload, name="material_upload"),
    path("<int:course_id>/feedback/", give_feedback, name="give_feedback"),
    path("status/", post_status, name="post_status"),
]
