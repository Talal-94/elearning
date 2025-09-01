from django.urls import path
from .views import (
    signup_view,
    CustomLoginView,
    logout_view,
    user_search_view,
    block_user,
    unblock_user,
    profile_view,
    notifications_list,
    notifications_unread_count,
    notifications_mark_all_read,
    edit_profile,
    notifications_recent_json
)

urlpatterns = [
    # Auth
    path("signup/", signup_view, name="signup"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),

    # Teacher user‑search & block/unblock
    path("users/search/", user_search_view, name="user_search"),
    path("users/<int:user_id>/block/", block_user, name="user_block"),
    path("users/<int:user_id>/unblock/", unblock_user, name="user_unblock"),

    # User profiles
    path("users/<str:username>/", profile_view, name="user_profile"),
    path("profile/edit/", edit_profile, name="edit_profile"),
    
    # Notifications
    path("notifications/", notifications_list, name="notifications_list"),
    path("notifications/unread-count/", notifications_unread_count, name="notifications_unread_count"),
    path("notifications/mark-all-read/", notifications_mark_all_read, name="notifications_mark_all_read"),
    path("notifications/recent-json/", notifications_recent_json, name="notifications_recent_json"),
]
