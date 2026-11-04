# Backend 2026 — Gestión de citas y servicios

API REST con FastAPI y SQLAlchemy para administrar clientes, servicios, profesionales y citas de un centro de atención.

## Equipo

| Integrante | Área |
|---|---|
| Camila Fuentes | Modelos ORM, relaciones y migraciones |
| Emily Jara | Clientes y servicios |
| Francisca Alvarado | Profesionales, reservas y reglas de agenda |
| Francisca Salazar | Integración e infraestructura |
| Isidora Valverde | Pruebas automatizadas y documentación |

## Arquitectura

- `app/main.py` crea la aplicación y registra los routers.
- `app/routers/` contiene los endpoints de clientes, citas y servicios.
- `app/schemas/` define los DTO y la validación de entrada y salida.
- `app/infrastructure/models/` contiene los modelos SQLAlchemy.
- `app/infrastructure/database.py` configura la conexión PostgreSQL desde variables de entorno.
- `migrations/` contiene las migraciones Alembic.
- `scripts/seed.py` agrega datos conectados de demostración de forma repetible.
- `tests/` contiene pruebas aisladas que usan SQLite en memoria.
- El modelo conceptual y relacional se describe en [`docs/diagrama-entidades.md`](docs/diagrama-entidades.md).

## Requisitos

- Python 3.10 o superior.
- Para ejecutar la aplicación: Docker Desktop con Docker Compose, o una instancia PostgreSQL disponible.
- Para ejecutar las pruebas: dependencias de `requirements-dev.txt`.

## Ejecutar con Docker Compose

Desde la raíz del repositorio:

```powershell
docker compose up --build -d
```

Compose inicia PostgreSQL y la API. El contenedor de la API aplica `alembic upgrade head` al iniciar. La configuración local de desarrollo usa `postgres` como usuario, contraseña y base de datos por defecto; para otros valores, crea `.env` a partir de `.env.example` y completa `DB_NAME`, `DB_USER` y `DB_PASSWORD`. No subas `.env` ni credenciales reales al repositorio.

- Swagger UI: <http://127.0.0.1:8000/docs>
- Esquema OpenAPI: <http://127.0.0.1:8000/openapi.json>

Para detener los contenedores sin eliminar los datos persistidos:

```powershell
docker compose down
```

Para eliminar también el volumen local de PostgreSQL, lo que borra sus datos:

```powershell
docker compose down -v
```

## Ejecutar localmente sin Docker

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Completa las cinco variables de `.env` con una base PostgreSQL disponible (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`). Luego aplica las migraciones, agrega los datos de demostración si se necesitan y levanta la API:

```powershell
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

## Pruebas automatizadas

Las pruebas crean una base SQLite temporal por caso, activan las claves foráneas y reemplazan la sesión de base de datos de la API. No necesitan PostgreSQL ni alteran la base de desarrollo.

```powershell
python -m pytest -q
```

En la última ejecución local documentada sobre esta rama: **43 aprobadas, 1 omitida y 0 fallidas**. La única omitida corresponde al CRUD HTTP de profesionales, cuyo router aún no está registrado en `app/main.py`. El alcance y el resultado por caso están en [`pruebas.md`](pruebas.md), y la matriz de requisitos está en [`docs/avance-isidora.md`](docs/avance-isidora.md).

## Endpoints registrados

La documentación interactiva de Swagger muestra los parámetros, DTO y códigos de respuesta descritos por la API.

| Recurso | Operaciones principales |
|---|---|
| `/clientes` | Listar, crear, consultar por ID, actualizar y eliminar |
| `/servicios` | Listar, crear, consultar por ID, actualizar, desactivar y restaurar |
| `/citas` | Listar, crear, consultar por ID, actualizar y eliminar |

Los errores de validación y negocio pueden responder con `400`, `404`, `409` o `422` según el endpoint. El `DELETE` de servicios realiza un borrado lógico.

## Estado y límites de la verificación

- La suite cubre CRUD de clientes y servicios; citas y agenda; relaciones y rollback; repetición del seeder; y el contrato OpenAPI.
- El CRUD HTTP de profesionales sigue pendiente de integración y por eso su prueba está omitida, no aprobada.
- Las pruebas de integración usan SQLite. La conexión PostgreSQL, migración desde una base vacía y persistencia tras reiniciar Docker requieren verificarse en el entorno del equipo.
- La matriz [`pruebas.md`](pruebas.md) distingue los resultados ejecutados de las verificaciones pendientes.
