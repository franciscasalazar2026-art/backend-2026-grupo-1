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