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
=======
# API REST - Sistema de Gestión de Citas y Servicios

API Backend desarrollada con FastAPI para la gestión de clientes, agendamiento de citas y servicios.

---

## Integrantes y Responsabilidades

| Estudiante | Área de Responsabilidad |
| :--- | :--- |
| Francisca Alvarado | Módulo de Clientes |
| Camila Fuentes | Módulo de Citas |
| Emily Jara | Módulo de Servicios |
| Francisca Salazar | Infraestructura y Base de Datos |
| Isidora Valverde | Documentación y Pruebas |

---

## Requisitos de Instalación y Ejecución

### 1. Clonar el repositorio
git clone https://github.com/franciscasalazar2026-art/backend-2026-grupo-1.git
cd backend-2026-grupo-1

### 2. Crear y activar un entorno virtual
python -m venv venv
# En Windows (PowerShell):
.\venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

### 3. Instalar dependencias
pip install -r requirements.txt

### 4. Levantar el servidor de desarrollo
uvicorn app.main:app --reload

Accede a la documentación interactiva en: http://127.0.0.1:8000/docs

---

## Poblado de Datos Iniciales (Seeder)

Para poblar la base de datos con el catálogo inicial de servicios y facilitar las pruebas locales:

python scripts/seed_data.py

> **Nota:** El script intenta conectar a PostgreSQL por defecto y cuenta con fallback automático a SQLite local para entorno de desarrollo.

---

## Pruebas Automatizadas (Pytest)

El proyecto cuenta con una suite de pruebas automatizadas con pytest que utiliza SQLite en memoria para validar las operaciones y DTOs de servicios.

Para ejecutar la suite de pruebas:

python -m pytest tests/test_servicios.py

---

## Contrato de Endpoints REST

### Clientes
| Método | Endpoint | Descripción | Código Éxito |
| :--- | :--- | :--- | :--- |
| GET | /clientes | Lista clientes con paginación | 200 OK |
| POST | /clientes | Registra un nuevo cliente | 201 Created |
| GET | /clientes/{id} | Obtiene detalle de un cliente | 200 OK |
| PUT | /clientes/{id} | Actualiza datos de un cliente | 200 OK |
| DELETE | /clientes/{id} | Elimina un cliente | 204 No Content |

### Citas
| Método | Endpoint | Descripción | Código Éxito |
| :--- | :--- | :--- | :--- |
| GET | /citas | Lista citas con filtros | 200 OK |
| POST | /citas | Agenda una nueva cita | 201 Created |
| GET | /citas/{id} | Obtiene detalle de una cita | 200 OK |
| PUT | /citas/{id} | Actualiza estado/fecha de cita | 200 OK |
| DELETE | /citas/{id} | Cancela/Elimina una cita | 204 No Content |

### Servicios
| Método | Endpoint | Descripción | Código Éxito |
| :--- | :--- | :--- | :--- |
| GET | /servicios | Lista servicios con soporte para paginación y búsqueda por nombre (?buscar=) | 200 OK |
| POST | /servicios | Registra un nuevo servicio | 201 Created |
| GET | /servicios/{id} | Obtiene detalle de un servicio por su ID | 200 OK |
| PUT | /servicios/{id} | Actualiza la información de un servicio | 200 OK |
| DELETE | /servicios/{id} | Desactiva un servicio mediante borrado lógico | 200 OK |
| PATCH | /servicios/{id}/restaurar | Reactiva un servicio desactivado previamente | 200 OK |
