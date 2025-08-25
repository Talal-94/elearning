# from django.shortcuts import render, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from courses.models import Course

# @login_required
# def room_view(request, room_name):
#     # room_name could be a course ID or slug
#     course = get_object_or_404(Course, pk=room_name)
#     return render(request, 'chat/room.html', {
#         'room_name': room_name,
#         'course': course,
#     })

# chat/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from courses.models import Course
from .permissions import can_access_course_chat

@login_required
def room(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    if not can_access_course_chat(request.user, course):
        from django.http import Http404
        raise Http404 
    return render(request, "chat/room.html", {"course": course})
