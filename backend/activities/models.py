import uuid

from django.db import models


class Activity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=160)
    starts_at = models.DateTimeField()
    capacity = models.PositiveIntegerField()

    class Meta:
        ordering = ("starts_at",)
        verbose_name_plural = "activities"

    def __str__(self):
        return self.title


class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)

    class Meta:
        verbose_name_plural = "participants"

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "enrollments"
        constraints = [
            models.UniqueConstraint(
                fields=("participant", "activity"),
                name="unique_enrollment",
            )
        ]

    def __str__(self):
        return f"{self.participant} -> {self.activity}"
