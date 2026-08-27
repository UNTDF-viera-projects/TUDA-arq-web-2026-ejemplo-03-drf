from datetime import datetime
from uuid import UUID

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Count
from django.shortcuts import render
from django.views.decorators.http import require_GET
from ninja import Header, NinjaAPI, Schema
from ninja.errors import ValidationError as NinjaValidationError
from pydantic import Field

from .models import Activity, Enrollment, Participant
from .representations import (
    serialize_activities,
    serialize_activity,
    serialize_enrollment,
    serialize_enrollments,
)


api = NinjaAPI(
    title="API de actividades e inscripciones",
    version="1.0.0",
    description=(
        "Primera versión funcional de la API de la Actividad 1. "
        "Las operaciones bajo /me usan el header X-Participant-ID como "
        "identidad controlada de demostración; no implementan autenticación real."
    ),
)


class ActivityOut(Schema):
    id: UUID = Field(description="Identificador único de la actividad.")
    title: str = Field(description="Nombre visible de la actividad.")
    starts_at: datetime = Field(
        description="Fecha y hora de inicio en formato ISO 8601.",
        examples=["2026-03-25T18:00:00-03:00"],
    )
    capacity: int = Field(
        ge=0,
        description="Cantidad máxima de participantes.",
        examples=[30],
    )
    available_slots: int = Field(
        ge=0,
        description="Cupos disponibles según las inscripciones persistidas.",
        examples=[29],
    )


class EnrollmentOut(Schema):
    activity_id: UUID = Field(description="Actividad en la que se inscribió.")
    participant_id: UUID = Field(description="Participante de la inscripción.")
    enrolled_at: datetime = Field(
        description="Fecha y hora de inscripción en formato ISO 8601.",
        examples=["2026-04-01T12:00:00-03:00"],
    )


class ErrorOut(Schema):
    code: str = Field(
        description="Código estable y legible por clientes.",
        examples=["activity_not_found"],
    )
    message: str = Field(
        description="Descripción del error.",
        examples=["La actividad no existe."],
    )


ACTIVITY_NOT_FOUND = {
    "code": "activity_not_found",
    "message": "La actividad no existe.",
}
INVALID_IDENTITY = {
    "code": "invalid_participant",
    "message": "Falta el header X-Participant-ID o no identifica a un participante.",
}
CAPACITY_EXHAUSTED = {
    "code": "capacity_exhausted",
    "message": "No hay cupos disponibles.",
}
INVALID_REQUEST = {
    "code": "invalid_request",
    "message": "PUT no recibe un body en esta versión.",
}
REQUEST_NOT_VALID = {
    "code": "invalid_request",
    "message": "Los parámetros del request no son válidos.",
}

PARTICIPANT_HEADER = Header(
    ...,
    alias="X-Participant-ID",
    description=(
        "UUID del participante de demostración. El comando seed_activities crea "
        "a3d8c92e-4f1a-4e5b-8c7d-9e0f1a2b3c4d."
    ),
    examples=["a3d8c92e-4f1a-4e5b-8c7d-9e0f1a2b3c4d"],
)


@api.exception_handler(NinjaValidationError)
def api_validation_error(request, exception):
    if any(error["loc"][0] == "header" for error in exception.errors):
        payload = INVALID_IDENTITY
    else:
        payload = REQUEST_NOT_VALID
    return api.create_response(request, payload, status=400)


def current_participant(participant_id):
    if not participant_id:
        return None

    try:
        return Participant.objects.get(id=participant_id)
    except (Participant.DoesNotExist, DjangoValidationError, ValueError):
        return None


@require_GET
def activity_list(request):
    activities = Activity.objects.all()
    return render(
        request,
        "activities/activity_list.html",
        {"activities": activities},
    )


@api.get(
    "/activities",
    response={200: list[ActivityOut], 405: None},
    summary="Listar actividades",
    description="Devuelve todas las actividades ordenadas por fecha de inicio.",
    tags=["Activities"],
    operation_id="listActivities",
)
def activity_api_list(request):
    activities = Activity.objects.annotate(
        enrolled_count=Count("enrollments")
    ).order_by("starts_at")
    return serialize_activities(activities)


@api.get(
    "/activities/{activity_id}",
    response={200: ActivityOut, 400: ErrorOut, 404: ErrorOut, 405: None},
    summary="Consultar una actividad",
    description="Recupera una actividad concreta a partir de su UUID.",
    tags=["Activities"],
    operation_id="getActivity",
)
def activity_api_detail(request, activity_id: UUID):
    try:
        activity = Activity.objects.annotate(
            enrolled_count=Count("enrollments")
        ).get(id=activity_id)
    except Activity.DoesNotExist:
        return 404, ACTIVITY_NOT_FOUND
    return serialize_activity(activity)


@api.get(
    "/me/enrollments",
    response={200: list[EnrollmentOut], 400: ErrorOut, 405: None},
    summary="Listar mis inscripciones",
    description=(
        "Lista las inscripciones del participante indicado por "
        "X-Participant-ID. Devuelve una colección vacía si no tiene inscripciones."
    ),
    tags=["Enrollments"],
    operation_id="listMyEnrollments",
)
def enrollment_api_list(
    request,
    participant_id: str = PARTICIPANT_HEADER,
):
    participant = current_participant(participant_id)
    if participant is None:
        return 400, INVALID_IDENTITY

    enrollments = Enrollment.objects.filter(participant=participant).order_by(
        "enrolled_at"
    )
    return serialize_enrollments(enrollments)


@api.put(
    "/me/enrollments/{activity_id}",
    response={
        200: EnrollmentOut,
        201: EnrollmentOut,
        400: ErrorOut,
        404: ErrorOut,
        409: ErrorOut,
        405: None,
    },
    summary="Inscribirme en una actividad",
    description=(
        "Crea una inscripción sin body. Responde 201 si la crea y 200 con la "
        "inscripción existente si se repite el mismo PUT."
    ),
    tags=["Enrollments"],
    operation_id="putMyEnrollment",
)
def enrollment_api_put(
    request,
    activity_id: UUID,
    participant_id: str = PARTICIPANT_HEADER,
):
    participant = current_participant(participant_id)
    if participant is None:
        return 400, INVALID_IDENTITY
    if request.body:
        return 400, INVALID_REQUEST

    with transaction.atomic():
        try:
            activity = Activity.objects.select_for_update().get(id=activity_id)
        except Activity.DoesNotExist:
            return 404, ACTIVITY_NOT_FOUND

        enrollment = Enrollment.objects.filter(
            participant=participant,
            activity=activity,
        ).first()
        if enrollment is not None:
            return 200, serialize_enrollment(enrollment)

        if activity.enrollments.count() >= activity.capacity:
            return 409, CAPACITY_EXHAUSTED

        enrollment = Enrollment.objects.create(
            participant=participant,
            activity=activity,
        )

    return 201, serialize_enrollment(enrollment)


@api.delete(
    "/me/enrollments/{activity_id}",
    response={204: None, 400: ErrorOut, 404: ErrorOut, 405: None},
    summary="Cancelar mi inscripción",
    description=(
        "Elimina la inscripción del participante y libera el cupo. "
        "La operación es idempotente y responde siempre 204 si la actividad existe."
    ),
    tags=["Enrollments"],
    operation_id="deleteMyEnrollment",
)
def enrollment_api_delete(
    request,
    activity_id: UUID,
    participant_id: str = PARTICIPANT_HEADER,
):
    participant = current_participant(participant_id)
    if participant is None:
        return 400, INVALID_IDENTITY

    try:
        activity = Activity.objects.get(id=activity_id)
    except Activity.DoesNotExist:
        return 404, ACTIVITY_NOT_FOUND

    Enrollment.objects.filter(
        participant=participant,
        activity=activity,
    ).delete()
    return 204, None
