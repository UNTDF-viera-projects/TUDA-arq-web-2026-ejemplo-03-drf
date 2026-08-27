from django.contrib import admin

from .models import Activity, Enrollment, Participant


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "starts_at", "capacity", "id")
    ordering = ("starts_at",)


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("name", "id")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("participant", "activity", "enrolled_at", "id")
    ordering = ("enrolled_at",)
