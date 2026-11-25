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
- `app/presentation/routers/` contiene los endpoints y las dependencias de autenticación.
- `app/presentation/schemas/dtos/` define los DTO y la validación de entrada y salida.
- `app/application/services/` coordina los casos de uso.
- `app/domain/` contiene entidades y reglas como la política de contraseña.
- `app/infrastructure/models/` contiene los modelos SQLAlchemy.
- `app/infrastructure/repositories/` implementa la persistencia y las transacciones.
- `app/infrastructure/database.py` configura la conexión PostgreSQL desde variables de entorno.
- `migrations/` contiene las migraciones Alembic.
- `scripts/seed.py` agrega datos conectados de demostración de forma repetible.
- `tests/` incluye unitarias, regresiones con SQLite, integración PostgreSQL y E2E por HTTP.
- El modelo conceptual y relacional se describe en [`docs/diagrama-entidades.md`](docs/diagrama-entidades.md).
- La revisión de imports, módulos legados y mappers está en [`docs/revision-arquitectura.md`](docs/revision-arquitectura.md).

## Requisitos

- Python 3.10 o superior.
- Para ejecutar la aplicación: Docker Desktop con Docker Compose, o una instancia PostgreSQL disponible.
- Para ejecutar las pruebas: dependencias de `requirements-dev.txt`.

## Ejecutar con Docker Compose

Desde la raíz del repositorio, inicia PostgreSQL y comprueba que esté disponible antes de migrar.

```powershell
docker compose up -d db
docker compose exec db pg_isready
docker compose run --rm --build web alembic upgrade head
docker compose up -d web
```

El contenedor inicia Uvicorn. Aplica Alembic explícitamente al crear la base o incorporar una revisión. Compose usa `postgres` como usuario y contraseña y `backend_db` como nombre de base por defecto. Estos valores se configuran mediante `DB_USER`, `DB_PASSWORD` y `DB_NAME` en un `.env` local.

- Swagger UI: <http://127.0.0.1:8000/docs>
- Esquema OpenAPI: <http://127.0.0.1:8000/openapi.json>

Para detener los contenedores sin eliminar los datos persistidos:

```powershell
docker compose down
```

Para revisar el arranque usa `docker compose logs web`. El volumen conserva los datos de PostgreSQL.

## Ejecutar localmente sin Docker

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Completa `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD` en `.env`. Configura `JWT_SECRET_KEY` con una clave privada de al menos 32 caracteres. Para ensayar recuperación en local, asigna `RECOVERY_MAIL_DIR` a una carpeta privada fuera del repositorio. Aplica las migraciones antes de iniciar la API.

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

La raíz `GET /` comprueba disponibilidad. Para preparar datos de demostración, usa `.\.venv\Scripts\python.exe -m scripts.seed` sobre una base local de desarrollo.

### Cuentas de demostración local

Después de aplicar las migraciones, ejecuta el seeder en esa misma base y abre Swagger en `/docs`. Las dos cuentas ficticias son:

| Rol | Correo | Contraseña de demostración |
| --- | --- | --- |
| Admin | `admin.demo@example.com` | `AdminDemo2026!` |
| Cliente | `cliente.demo@example.com` | `ClienteDemo2026!` |

En `POST /auth/login`, envía `email` y `password`. Copia únicamente el `access_token` a **Authorize** para consultar `/auth/me` y las operaciones protegidas. Una escritura de `/clientes` con cliente devuelve `403`; la misma petición con admin permite crear el recurso. El registro público siempre crea un cliente aunque se envíe `rol: admin`.

Estas credenciales corresponden al seeder local. Las pruebas generan cuentas independientes y verifican el login HTTP de ambas cuentas demo, sus roles y la ausencia de contraseña y hash en los perfiles. El seeder conserva usuarios existentes y no restablece sus contraseñas. Si antes se ejecutó la versión con correos `@example.test`, esas cuentas permanecen y se agregan las dos `@example.com`; una base nueva contiene solo las dos actuales. Repetirlo no agrega duplicados.

La política implementada exige al menos 12 caracteres tanto en registro como en recuperación. El plan describe además mezcla de caracteres; esa condición adicional requiere acordar el contrato con el equipo, pues el código y la pauta de 5.5 revisados exigen la longitud mínima. Las claves demo cumplen ambas descripciones.

## Pruebas automatizadas

Las unitarias y las regresiones HTTP en memoria se pueden ejecutar sin PostgreSQL.

Las pruebas completas requieren `TEST_POSTGRES_URL` hacia una base PostgreSQL local de pruebas. Cada caso de integración o E2E crea un esquema nuevo, aplica Alembic y elimina ese esquema al terminar. E2E levanta Uvicorn en un puerto local y envía solicitudes por HTTP.

```powershell
$backendPython = '.\.venv\Scripts\python.exe'
& $backendPython -m pytest -q tests/unit
& $backendPython -m pytest -q tests --ignore=tests/unit --ignore=tests/integration --ignore=tests/e2e

if (-not $env:TEST_POSTGRES_URL) { throw 'Configura TEST_POSTGRES_URL según pruebas.md' }
& $backendPython -m pytest -q tests/integration
& $backendPython -m pytest -q tests/e2e
& $backendPython -m pytest -q --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=85
```

La preparación de PostgreSQL, los casos por nivel y el resultado medido están en [`pruebas.md`](pruebas.md). La tabla de hallazgos y comprobaciones está en [`docs/retroalimentacion.md`](docs/retroalimentacion.md).

La consolidación de las tareas 3 y 4 está en el [informe de validación](docs/informe-validacion.md), con [evidencias de ejecución y estado de las capturas](docs/evidencias/2026-11-24/README.md) y una [matriz de los criterios de la rúbrica](docs/matriz-evidencias-rubrica.md). Para arranques E2E lentos puede definirse `E2E_STARTUP_TIMEOUT` en segundos. El valor predeterminado es 60 y admite valores mayores que cero y hasta 300.

## Endpoints registrados

La documentación interactiva de Swagger muestra los parámetros, DTO y códigos de respuesta descritos por la API.

| Recurso | Operaciones principales |
|---|---|
| `/clientes` | Listar, crear, consultar por ID, actualizar y eliminar |
| `/servicios` | Listar, crear, consultar por ID, actualizar, desactivar y restaurar |
| `/citas` | Listar, crear, consultar por ID, actualizar y eliminar |
| `/profesionales` | CRUD y asignación de servicios |
| `/auth` | Registro, login, usuario actual, renovación, logout y recuperación |

Los errores de validación y negocio pueden responder con `400`, `404`, `409` o `422` según el endpoint. El `DELETE` de servicios realiza un borrado lógico.

## Flujo de autenticación y recuperación

1. `POST /auth/registro` crea una cuenta con rol `cliente` y contraseña de al menos 12 caracteres. Para una demostración local puedes usar `demo@example.com` y una contraseña exclusiva de prueba. Los tests generan sus propios datos y crean el personal autorizado en la base desechable.
2. `POST /auth/login` devuelve un access JWT y un refresh opaco. Envía `Authorization: Bearer <access_token>` al consultar `/auth/me` o utilizar una operación protegida. Los endpoints de clientes exigen autenticación para lectura y rol `admin` o `recepcionista` para escritura. Las escrituras de servicios requieren `admin`. Una credencial ausente o inválida devuelve `401`. Un rol insuficiente devuelve `403`.
3. `POST /auth/refresh` rota el refresh y `POST /auth/logout` lo revoca. Ambos reciben `{"refresh_token": "…"}`. El access ya emitido conserva su vigencia hasta expirar salvo que se invalide su versión al cambiar la contraseña.
4. `POST /auth/forgot-password` recibe `{"email": "demo@example.com"}` y devuelve `200` con el mismo mensaje para ambas situaciones. En el taller, la aplicación deposita el token de una cuenta activa en el buzón local configurado.
5. `POST /auth/reset-password` recibe `{"token": "…", "nueva_password": "…"}`. Un único cambio confirma el consumo, el nuevo hash y la revocación de las sesiones previas. Reutilizar el mismo JWT devuelve `400` y otro enlace emitido antes del cambio devuelve `401`.

El buzón de archivos sirve para pruebas locales. El transporte de correo para un despliegue, el pipeline de CI y la publicación en Kubero se verifican en la fase de infraestructura. Mantén `.env`, los archivos del buzón y los tokens fuera del repositorio.

### Flujo de una Solicitud
`Petición HTTP` ➔ `Router (Presentación)` ➔ `Servicio (Aplicación)` ➔ `Repositorio / ORM (Infraestructura)` ➔ `Base de Datos` ➔ `Respuesta DTO`
