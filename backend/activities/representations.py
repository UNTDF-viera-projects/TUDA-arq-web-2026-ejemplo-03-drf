from django.utils import timezone


def serialize_activity(activity):
    enrolled_count = getattr(activity, "enrolled_count", None)
    if enrolled_count is None:
        enrolled_count = activity.enrollments.count()

    return {
        "id": str(activity.id),
        "title": activity.title,
        "starts_at": timezone.localtime(activity.starts_at).isoformat(),
        "capacity": activity.capacity,
        "available_slots": max(activity.capacity - enrolled_count, 0),
    }


def serialize_activities(activities):
    return [serialize_activity(activity) for activity in activities]


def serialize_enrollment(enrollment):
    return {
        "activity_id": str(enrollment.activity_id),
        "participant_id": str(enrollment.participant_id),
        "enrolled_at": timezone.localtime(enrollment.enrolled_at).isoformat(),
    }


def serialize_enrollments(enrollments):
    return [serialize_enrollment(enrollment) for enrollment in enrollments]
