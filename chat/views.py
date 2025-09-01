from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from courses.models import Course
from .permissions import can_access_course_chat
from .models import ChatMessage


@login_required
def room(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    if not can_access_course_chat(request.user, course):
        from django.http import Http404
        raise Http404

    history = (
        ChatMessage.objects
        .filter(course=course)
        .select_related("user")
        .order_by("created_at")[:200]
    )

    return render(
        request,
        "chat/room.html",
        {
            "course": course,
            "history": history,
            "me_id": request.user.id,                   
            "instructor_id": course.instructor_id,      
        },
    )
