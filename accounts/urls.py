from django.urls import path
from .views import (
    signup_view,
    CustomLoginView,
    logout_view,
    user_search_view,
    block_user,
    unblock_user,
    profile_view,
)

urlpatterns = [
    path("signup/", signup_view, name="signup"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),

    # Teacher user‑search & block/unblock
    path("users/search/", user_search_view, name="user_search"),
    path("users/<int:user_id>/block/", block_user, name="user_block"),
    path("users/<int:user_id>/unblock/", unblock_user, name="user_unblock"),

    # Public user profiles
    path("users/<str:username>/", profile_view, name="user_profile"),
]
