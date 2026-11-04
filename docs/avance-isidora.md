# Matriz de requisitos y avance — Isidora

Esta matriz registra el estado comprobado en la rama de cierre basada en `origin/main` (`223459c`). Los cambios de esta rama deben integrarse mediante revisión antes de considerarlos parte de `main`.

| Requisito | Estado | Evidencia / pendiente |
|---|---|---|
| Fixtures aislados con base de prueba y relaciones válidas | Probado | `tests/conftest.py`; SQLite temporal con claves foráneas activas. |
| Casos reproducibles de clientes, servicios, citas y agenda | Probado | `tests/test_clientes.py`, `tests/test_servicios.py` y `tests/test_citas.py`; resultados en [`../pruebas.md`](../pruebas.md). |
| Seeder con dos registros conectados por entidad y asociaciones | Probado | `tests/test_seed.py` ejecuta el seeder dos veces sobre una base de prueba limpia. |
| Repetibilidad de la suite sin datos manuales | Probado | Dos ejecuciones consecutivas de `python -m pytest -q`; ver salida en [`../pruebas.md`](../pruebas.md). |
| Swagger/OpenAPI: rutas, parámetros, DTO y códigos de respuesta | Probado en esta rama | `tests/test_openapi.py` consulta `/openapi.json`; los routers describen respuestas de error conocidas. |
| README de instalación, Compose, migraciones, seeder, arquitectura, endpoints y pruebas | Implementado en esta rama | [`../README.md`](../README.md); pasos documentados, sin afirmar verificaciones de PostgreSQL no ejecutadas. |
| Matriz de requisitos con estado y evidencia | Implementado en esta rama | Esta página; separa pruebas aprobadas y pendientes de integración. |
| Evidencias y pauta breve para la presentación | Implementado en esta rama | [`evidencias-presentacion-isidora.md`](evidencias-presentacion-isidora.md). |
| CRUD HTTP de profesionales y sus asignaciones | Pendiente de integración del equipo | El router `/profesionales` no está registrado en `app/main.py`; su prueba queda omitida y no aprobada. |
| Migración desde PostgreSQL vacío y persistencia tras reinicio | Pendiente de ejecutar en entorno PostgreSQL | La suite automatizada de esta entrega usa SQLite. Requiere coordinar y probar el entorno compartido. |
| Confirmar con el negocio las hipótesis P1–P3 | Pendiente | No presentar agenda manual, actores ni consecuencias como hechos hasta validarlos. |

## Alcance de la comprobación

- La última ejecución reproducible está registrada en [`../pruebas.md`](../pruebas.md), junto con el comando, el resultado y una matriz de entradas y respuestas observadas.
- Swagger UI se sirve en `/docs`; el documento que se valida automáticamente es `/openapi.json`.
- La base SQLite se crea y elimina en cada caso. Esto prueba reglas y relaciones de la aplicación, pero no sustituye las verificaciones de PostgreSQL.
- El diagrama conceptual y relacional está en [`diagrama-entidades.md`](diagrama-entidades.md). Los supuestos del problema siguen pendientes de confirmación.
