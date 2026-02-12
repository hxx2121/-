from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("django_auth.urls")),
    path("api/utils/", include("django_utils.urls")),
    path("api/qa/", include("django_qa.urls")),
]
