from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from courses.models import Course
from .models import ChatMessage
from .permissions import can_access_course_chat


@login_required
def room(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)

    # Access: instructor of course OR enrolled student (your helper enforces this)
    if not can_access_course_chat(request.user, course):
        # Keep your current behavior (404) rather than 403 if you prefer
        raise Http404

    # Load last 50 messages (oldest → newest for display)
    history_qs = (
        ChatMessage.objects.filter(course=course)
        .select_related("user")
        .order_by("-created_at")[:50]
    )
    history = list(history_qs)[::-1]

    return render(
        request,
        "chat/room.html",
        {
            "course": course,
            "history": history,
            "current_user_id": request.user.id,
        },
    )
