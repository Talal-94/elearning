from django.conf import settings
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .forms import SignUpForm
from .models import Block

User = get_user_model()

def is_teacher(user):
    return user.role == User.TEACHER

def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("home")

class CustomLoginView(LoginView):
    template_name = "accounts/login.html"

@login_required
@user_passes_test(is_teacher)
def user_search_view(request):
    q = request.GET.get("q", "").strip()
    users = []
    if q:
        users = User.objects.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q)
        ).exclude(pk=request.user.pk)
    blocked_ids = set(request.user.blocks_made.values_list("blocked_id", flat=True))
    results = [
        {"user": u, "is_blocked": (u.pk in blocked_ids)}
        for u in users
    ]
    return render(request, "accounts/user_search.html", {"results": results, "q": q})

@login_required
@user_passes_test(is_teacher)
def block_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    Block.objects.get_or_create(teacher=request.user, blocked=target)
    return redirect("user_search")

@login_required
@user_passes_test(is_teacher)
def unblock_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    Block.objects.filter(teacher=request.user, blocked=target).delete()
    return redirect("user_search")

@login_required
def profile_view(request, username):
    """
    Public profile page: show a user’s info, their status updates, and
    the courses they teach or are enrolled in.
    """
    profile_user = get_object_or_404(User, username=username)
    # fetch latest 10 status updates
    statuses = profile_user.status_updates.order_by('-created_at')[:10]

    if profile_user.role == User.TEACHER:
        items = profile_user.courses_taught.all()  # assuming related_name='courses_taught'
        item_label = "Courses Taught"
    else:
        enrollments = profile_user.enrollments.select_related('course').all()
        items = [e.course for e in enrollments]
        item_label = "Enrolled Courses"

    return render(request, "accounts/profile.html", {
        "profile_user": profile_user,
        "statuses": statuses,
        "items": items,
        "item_label": item_label,
    })
