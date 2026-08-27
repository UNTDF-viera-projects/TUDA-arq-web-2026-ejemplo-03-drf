from datetime import datetime
from uuid import UUID, uuid4

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Activity, Enrollment, Participant


class ApiContractTests(TestCase):
    def setUp(self):
        self.participant = Participant.objects.create(name="Ada")
        self.other_participant = Participant.objects.create(name="Grace")
        self.activity = Activity.objects.create(
            id=UUID("1b470ddf-3e84-4b77-9aae-091d21e52bd6"),
            title="Diseño de una API",
            starts_at=timezone.make_aware(datetime(2026, 3, 23, 18, 0)),
            capacity=2,
        )
        self.headers = {
            "HTTP_X_PARTICIPANT_ID": str(self.participant.id),
        }
        self.activity_url = f"/api/v1/activities/{self.activity.id}"
        self.enrollments_url = "/api/v1/me/enrollments"
        self.enrollment_url = (
            f"/api/v1/me/enrollments/{self.activity.id}"
        )

    def test_lists_activities_with_availability(self):
        Enrollment.objects.create(
            participant=self.other_participant,
            activity=self.activity,
        )

        response = self.client.get("/api/v1/activities")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": str(self.activity.id),
                    "title": "Diseño de una API",
                    "starts_at": "2026-03-23T18:00:00-03:00",
                    "capacity": 2,
                    "available_slots": 1,
                }
            ],
        )

    def test_gets_an_activity_and_reports_a_missing_one(self):
        response = self.client.get(self.activity_url)
        missing_response = self.client.get(
            f"/api/v1/activities/{uuid4()}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], str(self.activity.id))
        self.assertEqual(response.json()["available_slots"], 2)
        self.assertEqual(missing_response.status_code, 404)
        self.assertEqual(
            missing_response.json()["code"],
            "activity_not_found",
        )

    def test_personal_routes_reject_a_missing_or_unknown_identity(self):
        unknown_headers = {"HTTP_X_PARTICIPANT_ID": str(uuid4())}
        responses = [
            self.client.get(self.enrollments_url),
            self.client.put(self.enrollment_url),
            self.client.delete(self.enrollment_url, **unknown_headers),
        ]

        for response in responses:
            with self.subTest(method=response.request["REQUEST_METHOD"]):
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["code"],
                    "invalid_participant",
                )

    def test_lists_only_the_current_participant_enrollments(self):
        own = Enrollment.objects.create(
            participant=self.participant,
            activity=self.activity,
        )
        other_activity = Activity.objects.create(
            title="Otra actividad",
            starts_at=timezone.now(),
            capacity=1,
        )
        Enrollment.objects.create(
            participant=self.other_participant,
            activity=other_activity,
        )

        response = self.client.get(
            self.enrollments_url,
            **self.headers,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["activity_id"], str(self.activity.id))
        self.assertEqual(
            payload[0]["participant_id"],
            str(self.participant.id),
        )
        self.assertAlmostEqual(
            datetime.fromisoformat(payload[0]["enrolled_at"]).timestamp(),
            timezone.localtime(own.enrolled_at).timestamp(),
            delta=0.001,
        )

    def test_put_creates_an_idempotent_enrollment(self):
        created_response = self.client.put(
            self.enrollment_url,
            **self.headers,
        )
        repeated_response = self.client.put(
            self.enrollment_url,
            **self.headers,
        )

        self.assertEqual(created_response.status_code, 201)
        self.assertEqual(repeated_response.status_code, 200)
        self.assertEqual(repeated_response.json(), created_response.json())
        self.assertEqual(
            Enrollment.objects.filter(
                participant=self.participant,
                activity=self.activity,
            ).count(),
            1,
        )

    def test_put_rejects_a_body_and_an_activity_without_capacity(self):
        body_response = self.client.put(
            self.enrollment_url,
            data="{}",
            content_type="application/json",
            **self.headers,
        )
        self.activity.capacity = 1
        self.activity.save(update_fields=["capacity"])
        Enrollment.objects.create(
            participant=self.other_participant,
            activity=self.activity,
        )
        full_response = self.client.put(
            self.enrollment_url,
            **self.headers,
        )

        self.assertEqual(body_response.status_code, 400)
        self.assertEqual(body_response.json()["code"], "invalid_request")
        self.assertEqual(full_response.status_code, 409)
        self.assertEqual(full_response.json()["code"], "capacity_exhausted")

    def test_put_and_delete_report_a_missing_activity(self):
        url = f"/api/v1/me/enrollments/{uuid4()}"

        responses = [
            self.client.put(url, **self.headers),
            self.client.delete(url, **self.headers),
        ]

        for response in responses:
            with self.subTest(method=response.request["REQUEST_METHOD"]):
                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    response.json()["code"],
                    "activity_not_found",
                )

    def test_delete_is_idempotent_and_releases_the_slot(self):
        self.client.put(self.enrollment_url, **self.headers)

        first_response = self.client.delete(
            self.enrollment_url,
            **self.headers,
        )
        repeated_response = self.client.delete(
            self.enrollment_url,
            **self.headers,
        )
        activity_response = self.client.get(self.activity_url)

        self.assertEqual(first_response.status_code, 204)
        self.assertEqual(first_response.content, b"")
        self.assertEqual(repeated_response.status_code, 204)
        self.assertEqual(repeated_response.content, b"")
        self.assertEqual(activity_response.json()["available_slots"], 2)
        self.assertFalse(
            Enrollment.objects.filter(
                participant=self.participant,
                activity=self.activity,
            ).exists()
        )

    def test_routes_reject_methods_that_are_not_documented(self):
        responses = [
            self.client.post("/api/v1/activities"),
            self.client.put(self.activity_url),
            self.client.post(self.enrollments_url, **self.headers),
            self.client.post(self.enrollment_url, **self.headers),
        ]

        for response in responses:
            with self.subTest(path=response.request["PATH_INFO"]):
                self.assertEqual(response.status_code, 405)
                self.assertIn("Allow", response.headers)

    def test_openapi_exposes_the_complete_contract(self):
        docs_response = self.client.get("/api/v1/docs")
        schema_response = self.client.get("/api/v1/openapi.json")
        schema = schema_response.json()

        self.assertEqual(docs_response.status_code, 200)
        self.assertEqual(schema_response.status_code, 200)
        self.assertEqual(
            set(schema["paths"]),
            {
                "/api/v1/activities",
                "/api/v1/activities/{activity_id}",
                "/api/v1/me/enrollments",
                "/api/v1/me/enrollments/{activity_id}",
            },
        )
        enrollment_path = schema["paths"][
            "/api/v1/me/enrollments/{activity_id}"
        ]
        self.assertEqual(set(enrollment_path), {"put", "delete"})
        self.assertIn("409", enrollment_path["put"]["responses"])
        self.assertIn("204", enrollment_path["delete"]["responses"])
        header_parameters = schema["paths"]["/api/v1/me/enrollments"][
            "get"
        ]["parameters"]
        self.assertTrue(
            any(
                parameter["in"] == "header"
                and parameter["name"] == "X-Participant-ID"
                and parameter["required"] is True
                for parameter in header_parameters
            )
        )
        self.assertIn(
            "available_slots",
            schema["components"]["schemas"]["ActivityOut"]["properties"],
        )


class ClassicActivityListTests(TestCase):
    def test_lists_every_activity_field(self):
        activity = Activity.objects.create(
            id=UUID("1b470ddf-3e84-4b77-9aae-091d21e52bd6"),
            title="Diseño de una API",
            starts_at=timezone.make_aware(datetime(2026, 3, 23, 18, 0)),
            capacity=30,
        )

        response = self.client.get(reverse("activities:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(activity.id))
        self.assertContains(response, activity.title)
        self.assertContains(response, "2026-03-23T18:00:00-03:00")
        self.assertContains(response, "30")

    def test_rejects_non_get_requests(self):
        response = self.client.post(reverse("activities:list"))

        self.assertEqual(response.status_code, 405)
