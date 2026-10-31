# Guía y Documentación de Infraestructura Docker

Este documento especifica la arquitectura de contenedores y despliegue para la solución backend desarrollada en FastAPI y PostgreSQL.

## 1. Componentes del Entorno

- **FastAPI (Web App):** Servicio backend ejecutado sobre Python 3.10-slim y Uvicorn.
- **PostgreSQL 15 (Database):** Base de datos relacional para la persistencia de Clientes, Citas, Servicios y Profesionales.
- **Alembic:** Gestor de migraciones ejecutado automáticamente al iniciar el contenedor web.

## 2. Archivos Configurados

1. `Dockerfile`: Define la construcción de la imagen base, la instalación de dependencias nativas (`gcc`, `libpq-dev`) y dependencias Python de `requirements.txt`.
2. `docker-compose.yml`: Orquesta el ciclo de vida del servicio `web` y el servicio `db`, definiendo volúmenes de persistencia y variables de entorno.
3. `.dockerignore`: Optimiza el tiempo de construcción excluyendo archivos pesados o sensibles (`.git`, `.venv`, `__pycache__`).
4. `entrypoint.sh`: Garantiza la ejecución previa de las migraciones de Alembic antes de levantar el servidor.

## 3. Comandos de Operación

- **Despliegue completo:** `docker-compose up -d --build`
- **Monitoreo de logs:** `docker-compose logs -f web`
- **Detener infraestructura:** `docker-compose down`
