# Pruebas automatizadas y evidencia

## Preparación

Con Python 3.10 o superior, crea el entorno e instala las dependencias desde la raíz. La base de pruebas puede correr en una instalación local de PostgreSQL o en un contenedor.

```powershell
py -m venv .venv
$backendPython = '.\.venv\Scripts\python.exe'
& $backendPython -m pip install -r requirements-dev.txt
```

Para crear una instancia PostgreSQL local desechable con Docker:

```powershell
docker run --rm --detach --name backend-taller-test -p 127.0.0.1:55439:5432 -e POSTGRES_DB=backend_test -e POSTGRES_USER=backend_test -e POSTGRES_PASSWORD=taller-local postgres:15-alpine
docker exec backend-taller-test pg_isready -U backend_test -d backend_test
$env:TEST_POSTGRES_URL = 'postgresql+psycopg2://backend_test:taller-local@127.0.0.1:55439/backend_test'
```

`taller-local` es una contraseña desechable para el contenedor de ejemplo. Espera la confirmación de `pg_isready` antes de ejecutar los tests. Con PostgreSQL sin Docker, crea una base local exclusiva y ajusta la URL. La fixture requiere host local, puerto explícito, credenciales y un nombre distinguible de pruebas, como `backend_test`. El rol de pruebas necesita permiso para crear esquemas en esa base.

## Comandos por nivel

| Nivel | Qué ejecuta | Comando PowerShell |
| --- | --- | --- |
| Unitarias | Reglas, JWT, permisos, servicio aislado y buzón local | `& $backendPython -m pytest -q tests/unit` |
| Regresiones en memoria | Rutas de negocio, JWT y roles, seeder y contrato OpenAPI | `& $backendPython -m pytest -q tests --ignore=tests/integration --ignore=tests/e2e --ignore=tests/unit` |
| Integración | Alembic y transacciones sobre PostgreSQL real | `& $backendPython -m pytest -q tests/integration` |
| E2E | Uvicorn, HTTP externo, JWT y PostgreSQL real | `& $backendPython -m pytest -q tests/e2e` |

Las regresiones en memoria usan SQLite con claves foráneas y reemplazan la conexión. Para las pruebas con PostgreSQL, cada caso ejecuta Alembic en un esquema de nombre único y lo elimina al terminar. E2E arranca Uvicorn en un puerto libre y crea su propio buzón de recuperación. Las cuentas y contraseñas de cada caso se crean en la base de pruebas y se eliminan con el esquema.

Para ejecutar el conjunto y exigir 85% de cobertura de líneas de `app`:

```powershell
if (-not $env:TEST_POSTGRES_URL) { throw 'Configura la base PostgreSQL de pruebas' }
& $backendPython -m pytest -q --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=85 --junitxml=pytest-result.xml
```

El informe `coverage.xml` registra la cobertura por archivo. `pytest-result.xml` registra resultados por caso. Se incluye el código que ejecuta el proceso HTTP de Uvicorn. Sin `TEST_POSTGRES_URL`, pytest omite los casos de PostgreSQL y E2E, de modo que ese resultado sirve como comprobación rápida.

## Casos y evidencias

| Nivel | Casos representativos | Evidencia en el repositorio |
| --- | --- | --- |
| Unitarias | Longitud de contraseña, hash, JWT firmado y expirado, propósito incorrecto, roles, intentos y buzón sin filtraciones en logs | [tests/unit](tests/unit) |
| Regresión | CRUD autenticado de clientes y servicios, profesionales, DTO de citas de múltiples servicios, filtros y respuestas OpenAPI | [tests](tests) |
| Integración | Migración limpia, unicidad de correo, relaciones, rollback de citas, refresh rotado y reutilizado, revocación y recuperación concurrente | [tests/integration](tests/integration) |
| E2E acceso | Login, creación y consulta protegidas, rotación, logout y rechazo de renovación | [Escenarios HTTP](tests/e2e/test_auth_e2e.py) |
| E2E recuperación | Respuesta genérica, recepción en buzón, firma alterada, expiración, propósito incorrecto, uso único, segundo enlace anterior, login con clave nueva e invalidación de access y refresh previos | [Escenarios HTTP](tests/e2e/test_auth_e2e.py) |
| E2E permisos | Misma escritura comprobada con `401` sin token, `403` con cliente y `201` con admin, seguida de lectura del registro | [Escenarios HTTP](tests/e2e/test_auth_e2e.py) |

El resultado de 43 aprobadas y 1 omitida del [PR #17](https://github.com/franciscasalazar2026-art/backend-2026-grupo-1/pull/17) corresponde a la suite previa al JWT. En `0032403` se midieron 10 aprobadas, 33 fallos, 1 omisión y 49% de cobertura antes de los cambios.

## Resultado de esta revisión

| Nivel | Aprobadas | Fallidas | Omitidas |
| --- | ---: | ---: | ---: |
| Unitarias | 21 | 0 | 0 |
| Regresiones con SQLite | 61 | 0 | 0 |
| Integración PostgreSQL | 11 | 0 | 0 |
| E2E HTTP | 3 | 0 | 0 |
| **Total** | **96** | **0** | **0** |

La revisión del 24 de noviembre de 2026 pasó el umbral con **87,38% de cobertura de líneas en `app`** e incluyó el proceso Uvicorn de los escenarios E2E. Se ejecutó sobre `a931df8` con Python 3.13.15, PostgreSQL 18.6 y `-W error`, sin advertencias. La cifra de 88,26% indicada como antecedente en la tarea no se reprodujo con este commit y entorno.

Los [reportes de pytest, JUnit, cobertura y resumen](docs/evidencias/2026-11-24/README.md) permiten comprobar los conteos. El [informe de validación](docs/informe-validacion.md) registra las cinco advertencias de Starlette corregidas, los primeros errores de preparación E2E y el ajuste de plazo de arranque. Para equipos con arranque lento se puede definir `$env:E2E_STARTUP_TIMEOUT = '300'` antes del comando completo.

El resultado corresponde al conjunto de pruebas de esta rama. La [comprobación Docker complementaria](docs/evidencias/2026-11-24/docker-operacion.json) también verificó persistencia al recrear solo la API. La ejecución del pipeline y la operación en Kubero permanecen pendientes.
