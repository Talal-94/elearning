from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from .forms import SignUpForm, ProfileForm
from .models import Block
from courses.models import Course, Enrollment, StatusUpdate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Notification
from django.contrib import messages

User = get_user_model()


def is_teacher(user) -> bool:
    return getattr(user, "role", None) == User.TEACHER


def is_student(user) -> bool:
    return getattr(user, "role", None) == User.STUDENT


# -------- Auth --------
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


class CustomLogoutView(LogoutView):
    next_page = "home"


# -------- Search / Block --------
@login_required
def user_search_view(request):
    """Teacher directory search with initial list + pagination."""
    if not is_teacher(request.user):
        return HttpResponseForbidden()

    q = (request.GET.get("q") or "").strip()
    show_all = request.GET.get("all") == "1"
    page_num = request.GET.get("page")

    base_qs = User.objects.exclude(pk=request.user.pk).order_by("username")

    if q:
        qs = base_qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
        heading = f'Results for “{q}”'
        preface = None
    else:
        total = base_qs.count()
        qs = base_qs
        heading = "Users"
        preface = f"Showing the first 50 of {total} users. " if not show_all else f"Showing all {total} users."

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(page_num)

    if not q and not show_all:
        max_items = 50
        start_index = (page_obj.number - 1) * paginator.per_page
        end_index = min(start_index + paginator.per_page, max_items)
        if start_index >= max_items:
            page_obj.object_list = []
        else:
            page_obj.object_list = list(page_obj.object_list)[: end_index - start_index]

# Only consider blocked STUDENTS for the blocked_ids set
    blocked_ids = set(
        request.user.blocks_made
        .filter(blocked__role=User.STUDENT)
        .values_list("blocked_id", flat=True)
    )

    results = [
        {
            "user": u,
            "is_blocked": (u.pk in blocked_ids),
            "can_block": is_student(u),   # <- show/hide buttons in template
        }
        for u in page_obj.object_list
    ]
    
    context = {
        "q": q,
        "results": results,
        "page_obj": page_obj,
        "show_all": show_all,
        "heading": heading,
        "preface": preface,
    }
    return render(request, "accounts/user_search.html", context)


@login_required
def block_user(request, user_id):
    if not is_teacher(request.user):
        return HttpResponseForbidden("Only teachers can block users.")
    target = get_object_or_404(User, pk=user_id)

    if target.pk == request.user.pk:
        return HttpResponseForbidden("You cannot block yourself.")
    if not is_student(target):
        return HttpResponseForbidden("Only students can be blocked.")

    Block.objects.get_or_create(teacher=request.user, blocked=target)
    return redirect(request.META.get("HTTP_REFERER") or "user_search")


@login_required
def unblock_user(request, user_id):
    if not is_teacher(request.user):
        return HttpResponseForbidden("Only teachers can unblock users.")
    target = get_object_or_404(User, pk=user_id)

    if not is_student(target):
        return HttpResponseForbidden("Only students can be unblocked.")

    Block.objects.filter(teacher=request.user, blocked=target).delete()
    return redirect(request.META.get("HTTP_REFERER") or "user_search")


@login_required
def profile_view(request, username: str):
    profile_user = get_object_or_404(User, username=username)

    status_list = StatusUpdate.objects.filter(user=profile_user).order_by("-created_at")[:5]

    taught_courses = []
    enrolled_courses = []
    if getattr(profile_user, "role", None) == User.TEACHER:
        taught_courses = Course.objects.filter(instructor=profile_user).order_by("title")
    else:
        enrolled_courses = (
            Course.objects.filter(enrollments__student=profile_user)
            .distinct()
            .order_by("title")
        )

    context = {
        "profile_user": profile_user,
        "status_list": status_list,
        "taught_courses": taught_courses,
        "enrolled_courses": enrolled_courses,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def notifications_unread_count(request):
    count = Notification.objects.filter(recipient=request.user, read_at__isnull=True).count()
    return JsonResponse({"count": count})

@login_required
def notifications_list(request):
    qs = Notification.objects.filter(recipient=request.user).select_related("actor")[:50]
    return render(request, "accounts/notifications.html", {"notifications": qs})

@login_required
def notifications_mark_all_read(request):
    Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(read_at=timezone.now())
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect("notifications_list")


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("user_profile", username=request.user.username)
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/edit_profile.html", {"form": form})


@login_required
def notifications_recent_json(request):
    limit = int(request.GET.get("limit", "10"))
    qs = (request.user.notifications
            .order_by("-created_at")
            .values("verb", "url")[:limit])
    return JsonResponse({"results": list(qs)})
