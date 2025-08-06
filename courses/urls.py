# courses/urls.py
from django.urls import path
from .views import course_list, course_create, enroll_in_course, material_upload, give_feedback, post_status

urlpatterns = [
    path("", course_list, name="home"),
    path("create/", course_create, name="course_create"),
    path("<int:course_id>/enroll/", enroll_in_course, name="enroll"),
    path('<int:course_id>/materials/upload/', material_upload, name='material_upload'),
    path('<int:course_id>/feedback/', give_feedback, name='give_feedback'),
        path('status/', post_status, name='post_status'),



]
