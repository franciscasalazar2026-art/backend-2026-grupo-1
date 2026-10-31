#!/bin/sh
set -e

echo "=== Iniciando script de entrada (Entrypoint) ==="

# Esperar a que PostgreSQL esté completamente listo
if [ -n "$DB_HOST" ]; then
    echo "Esperando a la base de datos en $DB_HOST:$DB_PORT..."
    while ! nc -z $DB_HOST ${DB_PORT:-5432}; do
      sleep 1
    done
    echo "Base de datos disponible."
fi

# Ejecutar las migraciones de Alembic
echo "Ejecutando migraciones de base de datos..."
alembic upgrade head

# Iniciar la aplicación FastAPI
echo "Iniciando servidor de FastAPI..."
exec "$@"
