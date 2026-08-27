from datetime import datetime
from uuid import UUID

from django.core.management.base import BaseCommand
from django.utils import timezone

from activities.models import Activity, Participant


DEMO_PARTICIPANT = {
    "id": UUID("a3d8c92e-4f1a-4e5b-8c7d-9e0f1a2b3c4d"),
    "name": "Participante de demostración",
}


ACTIVITIES = [
    {
        "id": UUID("1b470ddf-3e84-4b77-9aae-091d21e52bd6"),
        "title": "Introducción a APIs web",
        "starts_at": timezone.make_aware(datetime(2026, 3, 23, 18, 0)),
        "capacity": 30,
    },
    {
        "id": UUID("6ccaf64f-d37e-4e6c-ae03-f3d6547bb297"),
        "title": "Contratos HTTP observables",
        "starts_at": timezone.make_aware(datetime(2026, 3, 25, 18, 0)),
        "capacity": 24,
    },
    {
        "id": UUID("80c08526-3da1-4f0a-845c-740fa33f1f50"),
        "title": "Taller de integración",
        "starts_at": timezone.make_aware(datetime(2026, 3, 27, 17, 0)),
        "capacity": 20,
    },
]


class Command(BaseCommand):
    help = "Restaura las actividades y el participante de demostración."

    def handle(self, *args, **options):
        Participant.objects.update_or_create(
            id=DEMO_PARTICIPANT["id"],
            defaults={"name": DEMO_PARTICIPANT["name"]},
        )

        expected_ids = [activity["id"] for activity in ACTIVITIES]
        Activity.objects.exclude(id__in=expected_ids).delete()

        for activity in ACTIVITIES:
            activity_id = activity["id"]
            defaults = {key: value for key, value in activity.items() if key != "id"}
            Activity.objects.update_or_create(id=activity_id, defaults=defaults)

        self.stdout.write(
            self.style.SUCCESS(
                f"Datos restaurados: {len(ACTIVITIES)} actividades, "
                "1 participante de demostración."
            )
        )
