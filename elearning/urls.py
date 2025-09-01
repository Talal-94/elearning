from django.contrib import admin
from django.urls import path, include
from courses.views import dashboard_view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),

    # Home = role-aware dashboard
    path("", dashboard_view, name="home"),

    # App routes
    path("", include("courses.urls")),
    path("", include("chat.urls")),

    # API
    path("api/", include("api.urls")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]

if settings.DEBUG or getattr(settings, "SERVE_MEDIA", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
