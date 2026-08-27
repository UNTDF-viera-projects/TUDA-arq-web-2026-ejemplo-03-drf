from django.contrib import admin
from django.urls import include, path

from activities.views import api



urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
    path("", include("activities.urls")),
]
