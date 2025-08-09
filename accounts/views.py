from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SignUpForm
from .models import Block

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
    """Teacher directory search.
    """
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
        if show_all:
            qs = base_qs
            heading = "All users"
            preface = f"Showing all {total} users."
        else:
            qs = base_qs
            heading = "Users"
            preface = f"Showing the first 50 of {total} users. "

    # pagination (25 per page)
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(page_num)

    # If no query and not show_all: cap to first 50 overall
    if not q and not show_all:
        # compute index range for first 50; if user navigates to page >2, it will still cap
        max_items = 50
        start_index = (page_obj.number - 1) * paginator.per_page
        end_index = min(start_index + paginator.per_page, max_items)
        # replace object_list with a sliced version when beyond max_items
        if start_index >= max_items:
            page_obj.object_list = []
        else:
            page_obj.object_list = list(page_obj.object_list)[: end_index - start_index]

    blocked_ids = set(
        request.user.blocks_made.values_list("blocked_id", flat=True)
    )
    results = [{"user": u, "is_blocked": (u.pk in blocked_ids)} for u in page_obj.object_list]

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
        return HttpResponseForbidden()
    target = get_object_or_404(User, pk=user_id)
    Block.objects.get_or_create(teacher=request.user, blocked=target)

    return redirect(request.META.get("HTTP_REFERER") or "user_search")


@login_required
def unblock_user(request, user_id):
    if not is_teacher(request.user):
        return HttpResponseForbidden()
    target = get_object_or_404(User, pk=user_id)
    Block.objects.filter(teacher=request.user, blocked=target).delete()
    return redirect(request.META.get("HTTP_REFERER") or "user_search")


# -------- Public Profile --------
@login_required
def profile_view(request, username: str):
    """Public user page visible to other users."""
    profile_user = get_object_or_404(User, username=username)
    return render(request, "accounts/profile.html", {"profile_user": profile_user})
