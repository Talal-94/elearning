from django.contrib import admin
from .models import Course, Enrollment, Material, Feedback, StatusUpdate

admin.site.register([Course, Enrollment, Material, Feedback, StatusUpdate])
