# Backend 2026 — Gestión de citas y servicios

API REST para gestionar clientes, citas y servicios de un centro atendido por profesionales. El repositorio está en transición desde una API inicial hacia persistencia en PostgreSQL con SQLAlchemy y migraciones Alembic.

> **Estado del avance:** el código de `main` contiene routers, modelos ORM y una migración inicial. La ejecución integrada depende de configurar PostgreSQL. En esta rama no hay `compose.yml` ni `.env` real; `.env.example` es solo una plantilla. No se debe afirmar que la conexión o la persistencia están probadas hasta ejecutar las verificaciones descritas en [`pruebas.md`](pruebas.md).

## Integrantes y áreas

| Integrante | Área de trabajo |
|---|---|
| Francisca Alvarado | Citas, profesionales y reglas de negocio |
| Camila Fuentes | Modelos ORM y relaciones |
| Emily Jara | CRUD de clientes y servicios |
| Francisca Salazar | Integración, configuración y Docker |
| Isidora Valverde | Diagrama, pruebas y documentación |

## Arquitectura actual

- `app/main.py` registra los routers de clientes, citas y servicios.
- `app/routers/` expone los endpoints y utiliza SQLAlchemy para leer y escribir.
- `app/infrastructure/database.py` lee `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD`, crea el engine y entrega una sesión por solicitud.
- `app/infrastructure/models/` contiene las tablas ORM.
- `app/domain/models.py` define el estado de una cita.
- `app/schemas/` contiene los DTO y esquemas de respuesta Pydantic.
- `migrations/` y `alembic.ini` contienen la configuración y la migración versionada.

El detalle de las entidades y sus cardinalidades está en [`docs/diagrama-entidades.md`](docs/diagrama-entidades.md). La estructura observada no contiene todavía un `compose.yml`; la matriz de avance distingue lo implementado de lo que falta integrar.

## Requisitos

- Python 3.10 o superior.
- PostgreSQL disponible y credenciales acordadas por el equipo.
- Dependencias de [`requirements.txt`](requirements.txt).
- Para pruebas automatizadas: dependencias de [`requirements-dev.txt`](requirements-dev.txt).

## Preparar el entorno local

1. Clona el repositorio y entra en la carpeta:

   ```powershell
   git clone https://github.com/franciscasalazar2026-art/backend-2026-grupo-1.git
   cd backend-2026-grupo-1
   ```

2. Crea y activa un entorno virtual, e instala las dependencias:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   ```

3. Copia `.env.example` a `.env` y completa los valores que el equipo confirme para PostgreSQL:

   ```powershell
   Copy-Item .env.example .env
   ```

   No subas `.env` ni contraseñas a GitHub. La plantilla deja las variables vacías intencionalmente porque no hay un `compose.yml` en `main` que confirme el nombre de la base, usuario o contraseña.

4. Con PostgreSQL en ejecución y `.env` completo, aplica la migración y levanta la API:

   ```powershell
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

   `alembic upgrade head` y `uvicorn` requieren una base de datos accesible. El comando de Docker queda pendiente hasta que se incorpore y valide el archivo Compose del equipo.

5. En otra terminal, crea los datos de demostración con `python scripts/seed.py`. El seeder es repetible y conserva registros que no identifica como datos de demostración.

6. Ejecuta las pruebas automatizadas con `python -m pytest -q`. Estas usan SQLite temporal y no necesitan la base PostgreSQL.

## Endpoints disponibles en el código

Los routers actuales no usan el prefijo `/api`.

| Recurso | Operaciones |
|---|---|
| `/clientes` | `GET`, `POST`, `GET /{cliente_id}`, `PUT /{cliente_id}`, `DELETE /{cliente_id}` |
| `/servicios` | `GET`, `POST` |
| `/citas` | `GET`, `POST`, `GET /{cita_id}`, `PUT /{cita_id}`, `DELETE /{cita_id}` |

El router de profesionales y las operaciones `GET` por ID, `PUT` y `DELETE` de servicios todavía no aparecen en `main`. Los casos preparados para esas rutas se dejan omitidos hasta integrar los cambios correspondientes.

La colección reproducible de solicitudes está en [`postman/isidora-clientes.postman_collection.json`](postman/isidora-clientes.postman_collection.json). La tabla de casos y los resultados observados están en [`pruebas.md`](pruebas.md).

## Problema y alcance por validar

La agenda manual, los actores afectados y las consecuencias descritas en la propuesta son **hipótesis de trabajo**, no hechos confirmados con el negocio. En [`docs/avance-isidora.md`](docs/avance-isidora.md) quedan marcados P1–P3 como pendientes de validación. El sistema no debe presentarse como solución de una situación real hasta confirmar esos puntos con el grupo y el negocio.

## Estado resumido

- **Preparado en esta rama:** documentación técnica, diagramas, plantilla de variables, seeder repetible y pruebas automatizadas.
- **Presente en el código de `main`:** rutas de clientes, citas y servicios; modelos SQLAlchemy; migración inicial.
- **Pendiente de evidencia:** conexión PostgreSQL, migración aplicada desde cero, Swagger y persistencia tras reinicio.
- **Pendiente de implementación/integración:** router de profesionales, operaciones restantes de servicios y reglas de agenda para fechas pasadas y traslapes.
- **Pendiente de integración:** configuración Docker/Compose y confirmación de P1–P3.
