# Backend 2026 — Gestión de citas y servicios

API REST desarrollada con FastAPI y SQLAlchemy para gestionar clientes, citas, profesionales y servicios de un centro de atención.

---

## Integrantes y Áreas de Responsabilidad

| Estudiante | Área de Responsabilidad |
| :--- | :--- |
| Francisca Alvarado | Módulo de Clientes |
| Camila Fuentes | Módulo de Citas |
| Emily Jara | Módulo de Servicios |
| Francisca Salazar | Infraestructura, Base de Datos y Docker |
| Isidora Valverde | Documentación y Pruebas |

---

## Arquitectura del Proyecto

- \pp/main.py\: Punto de entrada que registra todos los routers de la API.
- \pp/routers/\: Módulos que exponen los endpoints (\clientes\, \citas\, \servicios\, \profesionales\).
- \pp/infrastructure/database.py\: Gestión de conexión y sesiones de SQLAlchemy.
- \pp/infrastructure/models/\: Definición de tablas y relaciones ORM.
- \pp/schemas/\: Esquemas de validación y DTOs con Pydantic.
- \migrations/\: Historial de migraciones con Alembic.

El detalle de las entidades y sus cardinalidades está en [\docs/diagrama-entidades.md\ ](docs/diagrama-entidades.md).

---

## Requisitos de Instalación y Configuración

- Python 3.10 o superior.
- PostgreSQL disponible (o SQLite local para pruebas).
- Dependencias de [\equirements-dev.txt\ ](requirements-dev.txt).

### 1. Clonar el repositorio y preparar el entorno

\\\powershell
git clone https://github.com/franciscasalazar2026-art/backend-2026-grupo-1.git
cd backend-2026-grupo-1

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
\\\

### 2. Variables de Entorno

Copia la plantilla y configura tus credenciales locales:

\\\powershell
Copy-Item .env.example .env
\\\

### 3. Migraciones y Ejecución del Servidor

\\\powershell
alembic upgrade head
uvicorn app.main:app --reload
\\\

Documentación interactiva disponible en: \http://127.0.0.1:8000/docs\

---

## Poblado de Datos Iniciales (Seeder)

Para crear los datos de demostración y catálogo inicial:

\\\powershell
python -m scripts.seed
\\\

---

## Pruebas Automatizadas (Pytest)

Las pruebas ejecutan la suite automatizada utilizando una base de datos SQLite en memoria para validar las operaciones, reglas de negocio y esquemas DTO.

Para ejecutar la suite completa de pruebas:

\\\powershell
python -m pytest
\\\

> **Estado actual:** 42 pruebas aprobadas, 1 omitida (100% exitoso en \main\).

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
| GET | /servicios | Lista servicios con paginación y búsqueda (\?buscar=\) | 200 OK |
| POST | /servicios | Registra un nuevo servicio | 201 Created |
| GET | /servicios/{id} | Obtiene detalle de un servicio por su ID | 200 OK |
| PUT | /servicios/{id} | Actualiza la información de un servicio | 200 OK |
| DELETE | /servicios/{id} | Desactiva un servicio mediante borrado lógico | 200 OK |
| PATCH | /servicios/{id}/restaurar | Reactiva un servicio desactivado previamente | 200 OK |
