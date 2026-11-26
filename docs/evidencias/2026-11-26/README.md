# Evidencias Docker de Isidora Valverde del 26 de noviembre de 2026

Se construyó la API desde una copia limpia de Git de `256c6bbc7f91be5d34cfe6793cfc4f7311c4a242`, la misma revisión del código validada por las [107 pruebas del 25 de noviembre](../2026-11-25/README.md). Esta comprobación acredita operación local con Docker; la suite completa se ejecutó por separado con Python 3.13.15 y PostgreSQL 18.6 nativo.

## Resultado observado

- Tres servicios activos: API, PostgreSQL con healthcheck `healthy` y Adminer. Los puertos se publican únicamente en `127.0.0.1`.
- API, Swagger, OpenAPI y Adminer disponibles; salud devuelve HTTP 200 y `{"status":"ok","version":"1.0.0"}`. OpenAPI contiene 19 rutas distintas y 32 operaciones.
- Python 3.10.22 y PostgreSQL 15.20 en este entorno. Alembic está en `c4d987ee6f20`, con once tablas.
- La actualización del volumen de demostración anterior convirtió los dos correos `.test` a `.com`, conservando IDs, hashes y estado de seguridad. Las dos cuentas demo completaron login, consulta del perfil y logout con HTTP 200; no se conservan sus tokens.
- Tras `docker compose up -d --no-deps --force-recreate web`, cambió el contenedor de la API. PostgreSQL, Adminer, volumen, migración, tablas, conteos e IDs permanecieron iguales. La salud volvió a responder HTTP 200.

| Archivo | Evidencia |
| --- | --- |
| [docker.jpg](docker.jpg) | Docker Desktop con los tres servicios en ejecución y sus puertos. |
| [swagger.jpg](swagger.jpg) | Interfaz Swagger de la API en ejecución. |
| [swagger-salud.jpg](swagger-salud.jpg) | Solicitud real de salud, código 200 y cuerpo de respuesta. |
| [postgresql-tablas.jpg](postgresql-tablas.jpg) | Las once tablas del esquema `public` en Adminer. |
| [postgresql.jpg](postgresql.jpg) | Consulta de versión, migración y conteos: dos usuarios, clientes, profesionales y servicios; tres reservas y citas. |
| [docker-operacion.json](docker-operacion.json) | Revisión, imagen, servicios antes/después, persistencia y comprobaciones de cuentas demo, sin secretos. |
| [compose.evidencias.yml](compose.evidencias.yml) | Configuración complementaria utilizada, con variables privadas y puertos locales. |

La imagen web observada tiene ID `sha256:e09c817728a53b9daef5eb1c2bb9d5544ad03c90fe06cfc0a32a3e9900ef7e86`. Las capturas son de las interfaces reales; solo muestran datos ficticios, conteos y metadatos.

## Repetir la comprobación

En una carpeta local de trabajo, coloca `compose.evidencias.yml` junto a una carpeta llamada `source-256c6bb`. Desde un clon del repositorio, extrae el código versionado en esa carpeta:

```powershell
git archive --format=tar --output=backend-source.tar 256c6bbc7f91be5d34cfe6793cfc4f7311c4a242
New-Item -ItemType Directory -Path source-256c6bb
tar -xf backend-source.tar -C source-256c6bb
```

Configura en un `.env` privado junto al Compose `EVIDENCE_DB_PASSWORD` y `EVIDENCE_JWT_SECRET` con valores locales propios, y `EVIDENCE_REVISION=256c6bbc7f91be5d34cfe6793cfc4f7311c4a242`. Si el volumen ya existe, utiliza su contraseña vigente. Mantén ese archivo fuera de Git. Con los puertos 55440, 8008 y 8088 disponibles:

```powershell
docker compose -f compose.evidencias.yml build web
docker compose -f compose.evidencias.yml up -d db adminer
docker compose -f compose.evidencias.yml run --rm web alembic upgrade head
docker compose -f compose.evidencias.yml run --rm web python -m scripts.seed
docker compose -f compose.evidencias.yml up -d web
docker compose -f compose.evidencias.yml ps
```

Abre Swagger en `http://127.0.0.1:8008/docs` y Adminer en `http://127.0.0.1:8088`. En Adminer selecciona PostgreSQL, servidor `db`, usuario `evidencia`, base `backend_evidencias_test` y la contraseña de tu `.env`. La consulta conservada en la captura no muestra filas de usuarios ni credenciales. Las cuentas demo y su uso local están descritos en el [README principal](../../../README.md).

Registra migración, conteos e IDs antes de recrear únicamente `web` con `docker compose -f compose.evidencias.yml up -d --no-deps --force-recreate web`, y compáralos después. Un volumen nuevo produce datos semilla nuevos; la migración de correos antiguos requiere las cuentas demo de la revisión previa, como ocurrió en el volumen reutilizado. Los IDs y tiempos concretos pueden diferir.

Las etiquetas base `python:3.10-slim`, `postgres:15-alpine` y `adminer:4`, así como las dependencias no fijadas, pueden recibir actualizaciones. Reconstruir acredita el comportamiento del nuevo entorno, sin garantizar el mismo digest ni las versiones aquí registradas.

## Alcance del cierre

Esta evidencia resuelve la captura de Docker Desktop que quedó pendiente el 25 de noviembre por Windows bloqueado y actualiza el entorno complementario de `a931df8` a `256c6bb`. Se conservan los [antecedentes del 24](../2026-11-24/README.md) y los [resultados de pruebas del 25](../2026-11-25/README.md) con sus fechas y revisiones.

El Compose principal, el pipeline y Kubero mantienen los pendientes de la [matriz de rúbrica](../../matriz-evidencias-rubrica.md). El `version: 1.0.0` de la respuesta de salud es metadato de la API; no acredita una etiqueta Git `v1.0`, una ejecución de CI ni un despliegue institucional.
