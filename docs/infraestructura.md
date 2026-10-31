# Guía de Infraestructura y Despliegue con Docker

Este documento describe la configuración de entorno y contenedorización del proyecto para el grupo de desarrollo.

## Componentes Configurados

- **Dockerfile:** Define la imagen base con Python 3.10-slim e instala las dependencias de `requirements.txt`.
- **docker-compose.yml:** Define la orquestación entre la API FastAPI y la base de datos PostgreSQL 15.
- **.dockerignore:** Excluye entornos virtuales, archivos temporales y `.env` de la imagen para optimizar el peso del contenedor.
- **entrypoint.sh:** Aplica las migraciones de Alembic (`alembic upgrade head`) previo al inicio del servidor.
