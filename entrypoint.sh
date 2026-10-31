#!/bin/sh
echo "Ejecutando migraciones de la base de datos..."
alembic upgrade head

echo "Iniciando servidor FastAPI..."
exec "$@"
