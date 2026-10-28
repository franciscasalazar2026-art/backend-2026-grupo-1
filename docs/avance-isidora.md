# Avance de Isidora — pruebas, seeder y documentación

**Fecha de revisión:** 28-10-2026  
**Base revisada:** rama `main`, commit `1a1864a`  
**Alcance:** diagrama, suite de pruebas aislada, seeder repetible, README y matriz con resultados reales.

## Problema y supuestos por validar

El plan propone la hipótesis de que un negocio agenda manualmente y mantiene separados los datos de clientes, servicios y profesionales. No se ha registrado en este avance una confirmación con el negocio; por eso P1–P3 siguen siendo **hipótesis**, no hechos.

| Punto | Hipótesis de trabajo | Estado | Evidencia necesaria |
|---|---|---|---|
| P1 — Situación | Las citas se coordinan manualmente y los datos están repartidos en varias fuentes. | Pendiente de confirmar | Conversación con el negocio y nota de lo que realmente ocurre. |
| P2 — Actores | Clientes, recepción/personal administrativo y profesionales se ven afectados. | Pendiente de confirmar | Confirmar qué roles participan y qué información necesita cada uno. |
| P3 — Consecuencia | Podrían existir traslapes, datos inconsistentes o tiempo perdido buscando/confirmando citas. | Pendiente de confirmar | Identificar cuáles consecuencias ocurren de verdad; no presentarlas como constatadas. |

## Matriz de avance

| Entregable | Estado | Evidencia / pendiente |
|---|---|---|
| Diagrama conceptual de Cliente, Servicio, Profesional y Cita | Preparado | [`diagrama-entidades.md`](diagrama-entidades.md), con claves y relaciones 1:N propuestas. |
| Diagrama relacional del código actual | Preparado | El esquema físico incluye `reservas` y `profesional_servicios`; no se confunde con el modelo conceptual. |
| P1–P3 revisados con el negocio | Pendiente | No marcar como validado hasta tener confirmación del grupo/negocio. |
| README coherente con los archivos de `main` | Preparado en esta rama | Se retiraron los marcadores de conflicto y se documentó el estado sin afirmar persistencia probada. |
| Pruebas de clientes y servicios integrados | Aprobadas en SQLite temporal | `tests/test_clientes.py` y `tests/test_servicios.py`; ver resultados en [`pruebas.md`](../pruebas.md). |
| Pruebas de citas y rollback de reserva/cita | Aprobadas en SQLite temporal | `tests/test_citas.py`; el rollback queda verificado con error inyectado. |
| Asociación profesional-servicio | Restricción ORM probada | `tests/test_profesionales.py`; el CRUD HTTP sigue pendiente porque no existe router en `main`. |
| Seeder reproducible | Aprobado en SQLite temporal | `scripts/seed.py` conserva dos registros conectados por entidad al ejecutarse dos veces. |
| Rutas de servicios no integradas y CRUD profesional | Preparadas y omitidas | La suite deja casos skip hasta integrar los routers; no se cuentan como aprobados. |
| `.env.example` sin secretos | Preparado como plantilla | Variables derivadas de `app/infrastructure/database.py`; los valores siguen vacíos hasta confirmar Compose/credenciales. |
| Docker Compose / PostgreSQL integrado | Pendiente | No hay `compose.yml`/`compose.yaml` en `main`; no se levantaron contenedores. |
| OpenAPI generado con FastAPI `TestClient` | Verificado localmente | `GET /openapi.json` respondió `200` y publicó los routers esperados; se usaron variables temporales de importación, sin conectar a PostgreSQL. |
| API y Swagger ejecutados contra PostgreSQL | Pendiente | Las pruebas actuales usan SQLite. La aplicación requiere las cinco variables DB y un servidor alcanzable. |
| Migración Alembic aplicada | Pendiente de verificación | Hay una migración versionada; no se confirmó `alembic upgrade head` en una base real. |
| Persistencia tras reinicio | Pendiente de prueba | Requiere crear un cliente, reiniciar API y consultar el mismo ID con PostgreSQL configurado. |

## Decisiones de documentación

- Los endpoints que existen en el código son `/clientes`, `/citas` y `/servicios`; no se documenta un prefijo `/api`.
- El router de citas persiste una `ReservaORM` y una `CitaORM` en una transacción. La respuesta aplana cliente, servicio y profesional, aunque el esquema relacional usa claves foráneas indirectas.
- La colección Postman prepara respuestas esperadas; los scripts de Postman no equivalen a resultados ejecutados.
- La plantilla `.env.example` enumera solo las variables que ya lee el módulo de conexión. No incluye contraseñas reales ni inventa valores de Compose.

## Próximos pasos de integración

1. Acordar los valores y el servicio PostgreSQL con quien coordina la integración; añadir Compose solo desde esa configuración confirmada.
2. Copiar `.env.example` a `.env`, completar valores localmente y ejecutar la API y Alembic.
3. Correr la colección Postman y reemplazar `No ejecutado` en [`pruebas.md`](../pruebas.md) únicamente con códigos/resultados observados.
4. Validar P1–P3 con el negocio y actualizar el alcance si la hipótesis no corresponde.
