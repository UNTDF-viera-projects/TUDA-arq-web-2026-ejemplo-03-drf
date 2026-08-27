# Backend Django y API OpenAPI

Aplicación Django con persistencia SQLite. La ruta `/` conserva la vista HTML clásica y `/api/v1` expone la API documentada con Django Ninja.

## Requisitos

- Python 3.12 o posterior.

## Iniciar el proyecto

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_activities
python manage.py runserver
```

Abrir <http://127.0.0.1:8000/>. La documentación interactiva está en <http://127.0.0.1:8000/api/v1/docs> y el documento OpenAPI JSON en <http://127.0.0.1:8000/api/v1/openapi.json>.

`seed_activities` se puede ejecutar más de una vez: restaura el mismo conjunto de actividades y el participante de demostración sin duplicarlos.

## Contrato HTTP

| Método | Ruta | Éxito |
| --- | --- | --- |
| `GET` | `/api/v1/activities` | `200`, colección con cupos disponibles |
| `GET` | `/api/v1/activities/{activity_id}` | `200`, actividad |
| `GET` | `/api/v1/me/enrollments` | `200`, inscripciones propias |
| `PUT` | `/api/v1/me/enrollments/{activity_id}` | `201` al crear o `200` si ya existía |
| `DELETE` | `/api/v1/me/enrollments/{activity_id}` | `204`, sin body |

Las operaciones bajo `/me` requieren `X-Participant-ID`. El participante creado por el seed tiene UUID `a3d8c92e-4f1a-4e5b-8c7d-9e0f1a2b3c4d`. Una identidad ausente o desconocida produce `400`; una actividad inexistente, `404`; y una actividad sin cupos, `409`. Los métodos no habilitados producen `405`.

Ejemplo del recorrido completo:

```bash
PARTICIPANT_ID=a3d8c92e-4f1a-4e5b-8c7d-9e0f1a2b3c4d
ACTIVITY_ID=1b470ddf-3e84-4b77-9aae-091d21e52bd6

curl -i http://127.0.0.1:8000/api/v1/activities
curl -i http://127.0.0.1:8000/api/v1/activities/$ACTIVITY_ID
curl -i -H "X-Participant-ID: $PARTICIPANT_ID" http://127.0.0.1:8000/api/v1/me/enrollments
curl -i -X PUT -H "X-Participant-ID: $PARTICIPANT_ID" http://127.0.0.1:8000/api/v1/me/enrollments/$ACTIVITY_ID
curl -i -X DELETE -H "X-Participant-ID: $PARTICIPANT_ID" http://127.0.0.1:8000/api/v1/me/enrollments/$ACTIVITY_ID
```

Crear una inscripción inserta una fila en `activities_enrollment`; cancelarla elimina esa fila. `activities_activity` no se modifica: `available_slots` se calcula desde `capacity` y el conteo de inscripciones.

## Comandos útiles

```bash
# Ejecutar las pruebas
python manage.py test

# Abrir la consola de Django
python manage.py shell

# Vaciar la base y volver a cargar los datos de muestra
python manage.py flush --noinput
python manage.py seed_activities
```

## Estructura relevante

- `activities/models.py`: modelos `Activity`, `Participant` y `Enrollment`.
- `activities/views.py`: vista clásica, endpoints, esquemas y metadatos OpenAPI.
- `activities/representations.py`: representaciones JSON públicas.
- `activities/templates/activities/activity_list.html`: documento HTML producido por Django.
- `activities/management/commands/seed_activities.py`: datos reproducibles.

SQLite usa el archivo `db.sqlite3`, creado por `python manage.py migrate` y excluido de Git.
