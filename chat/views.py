from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from courses.models import Course

@login_required
def room_view(request, room_name):
    # room_name could be a course ID or slug
    course = get_object_or_404(Course, pk=room_name)
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'course': course,
    })
