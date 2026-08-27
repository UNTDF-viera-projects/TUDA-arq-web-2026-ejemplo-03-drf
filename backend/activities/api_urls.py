from django.urls import path

from .views import (
    ActivityDetailView,
    ActivityListView,
    EnrollmentDetailView,
    EnrollmentListView,
)


urlpatterns = [
    path("activities", ActivityListView.as_view(), name="api-activity-list"),
    path(
        "activities/<str:activity_id>",
        ActivityDetailView.as_view(),
        name="api-activity-detail",
    ),
    path(
        "me/enrollments",
        EnrollmentListView.as_view(),
        name="api-enrollment-list",
    ),
    path(
        "me/enrollments/<str:activity_id>",
        EnrollmentDetailView.as_view(),
        name="api-enrollment-detail",
    ),
]
