# Plan y evidencia de pruebas

Este documento diferencia las solicitudes preparadas de las pruebas que efectivamente se ejecutaron. La colección Postman está en [`postman/isidora-clientes.postman_collection.json`](postman/isidora-clientes.postman_collection.json).

## Estado del entorno al 28-10-2026

La revisión de `main` encontró que `app/infrastructure/database.py` exige `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD`. El repositorio no contiene un `.env` ni `compose.yml`/`compose.yaml`; la plantilla `.env.example` de esta rama deja los valores vacíos. Por ello **no se han ejecutado solicitudes HTTP contra PostgreSQL** y los resultados siguientes no se inventan.

## Verificaciones ejecutadas en esta rama

| Verificación | Resultado observado | Alcance |
|---|---|---|
| Compilación de `app/` y `migrations/` con Python 3.13 | Correcta, sin errores de sintaxis. | No valida conexión ni comportamiento de la base de datos. |
| Lectura JSON de la colección Postman | Correcta. | Valida estructura JSON; no ejecuta las solicitudes. |
| FastAPI `TestClient` — `GET /openapi.json` | `200`; OpenAPI contiene `/clientes`, `/citas` y `/servicios` (5 rutas en total). | Se usaron valores temporales no secretos solo para importar la app; no se conectó a PostgreSQL ni se probaron operaciones CRUD. |
| `git diff --check` | Sin errores de espacios en blanco. | Git informó solo conversión normal de fin de línea LF/CRLF en Windows. |

## Casos preparados

| ID | Solicitud / entrada | Resultado esperado por el código | Resultado obtenido | Estado |
|---|---|---|---|---|
| C01 | `POST /clientes` con nombre, email y teléfono válidos | `201`, respuesta de cliente con `id` | No ejecutado: falta configuración DB local y servicio PostgreSQL confirmado. | Bloqueado |
| C02 | `GET /clientes?limit=1&offset=0` | `200`, objeto paginado con `items`, `total`, `pagina`, `limite` y `total_paginas` | No ejecutado: mismo bloqueo de conexión. | Bloqueado |
| C03 | Repetir `POST /clientes` usando el correo de C01 | `409`, correo duplicado | No ejecutado: requiere que C01 se registre en DB. | Bloqueado |
| C04 | `POST /clientes` con email inválido | `422`, error de validación Pydantic | No ejecutado: la API no se pudo levantar sin DB. | Bloqueado |
| C05 | `GET /clientes/999999999` (ID inexistente) | `404`, cliente no encontrado | No ejecutado: la API no se pudo levantar sin DB. | Bloqueado |
| C06 | `POST /citas` con `cliente_id` inexistente y servicio/profesional de prueba | `400`, cliente inexistente | No ejecutado: la API no se pudo levantar sin DB. | Bloqueado |
| C07 | `GET /citas?estado=pendiente&ordenar_por=fecha_hora&direccion=asc&pagina=1&limite=10` | `200`, respuesta paginada y ordenada | No ejecutado: requiere DB. | Bloqueado |
| C08 | Crear cliente, reiniciar API y consultar `GET /clientes/{id}` | `200` y el mismo registro si persiste en PostgreSQL | No ejecutado: requiere conexión DB configurada y disponible. | Pendiente de integración |

## Comprobación estática del código

Estos puntos se observaron en los archivos de `main`; no son una prueba de ejecución:

- `GET /clientes` calcula `total` antes de aplicar `offset` y `limit` y devuelve metadatos de paginación.
- `POST /clientes` confirma la escritura con `db.commit()` y hace `db.rollback()` ante `IntegrityError`.
- `POST /citas` crea `ReservaORM` y `CitaORM` dentro de la misma transacción; usa `flush()`, `commit()` y `rollback()` ante conflicto de integridad.
- `GET /citas` ofrece filtro por estado, orden, dirección, página y límite.
- Hay modelos ORM y una migración inicial en el repositorio; todavía no se verificó la migración en una base de datos.

## Cómo ejecutar cuando PostgreSQL esté configurado

1. Completar `.env` con los valores confirmados por el equipo (no compartirlos ni subirlos a Git).
2. Iniciar PostgreSQL usando el procedimiento acordado; `compose.yml` aún no está en la rama `main` revisada.
3. Ejecutar `alembic upgrade head` y luego `uvicorn app.main:app --reload`.
4. Importar la colección en Postman, seleccionar `POST /clientes` y luego ejecutar las solicitudes de la colección en orden.
5. Registrar aquí fecha, entorno, código HTTP real y resultado observado. Si una prueba falla, conservar el error exacto y dejar el estado como fallido/bloqueado hasta corregirlo.

Los criterios finales de filtros, reglas de traslape y persistencia siguen pendientes de ejecución; la hipótesis de negocio también debe validarse antes de presentar resultados como hechos.
