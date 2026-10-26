from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/companies/", include("apps.companies.urls")),
]
