from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/documents/", include("documents.urls")),
    path("api/users/", include("users.urls")),
    path("api/tests/", include("tests.urls")),
]
