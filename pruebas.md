# Pruebas automatizadas y evidencia

## Cómo reproducir

En PowerShell, desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest -q
```

La suite usa SQLite en memoria, crea las tablas ORM y habilita las claves foráneas. Cada prueba recibe una base limpia; el seeder se prueba dos veces sobre esa misma base para comprobar que no depende de datos creados manualmente. No se requieren credenciales PostgreSQL.

## Última ejecución registrada

Entorno: Python 3.13, Windows, entorno virtual del proyecto. Se ejecutó `python -m pytest -q` dos veces consecutivas:

```text
43 passed, 1 skipped
43 passed, 1 skipped
```

Resultado: **86 aprobaciones en las dos ejecuciones, 2 omisiones (la misma prueba de profesionales en cada ejecución), 0 fallos**. La prueba omitida verifica el CRUD HTTP de profesionales, pero el router `/profesionales` todavía no está registrado en `app/main.py`; por eso no se contabiliza como aprobada.

## Casos representativos

| ID | Entrada y comprobación | Esperado | Observado | Estado |
|---|---|---:|---:|---|
| CLI-01 | Crear cliente y consultarlo por ID | `201`, luego `200` | `201`, luego `200`; email conservado | Aprobado |
| CLI-02 | Crear otro cliente con correo duplicado | `409` | `409` | Aprobado |
| CLI-03 | Crear cliente con correo inválido | `422` | `422` | Aprobado |
| CLI-04 | Consultar cliente inexistente | `404` | `404` | Aprobado |
| CLI-05 | Listar clientes con paginación | `200`, total y página coherentes | `200`, total 3 y 2 elementos | Aprobado |
| SER-01 | Crear y listar servicio | `201`, luego `200` | `201`, luego `200` | Aprobado |
| SER-02 | Consultar servicio inexistente | `404` | `404` | Aprobado |
| SER-03 | Actualizar servicio existente e inexistente | `200`, `404` | `200`, `404` | Aprobado |
| SER-04 | Desactivar servicio existente e inexistente | `204`, `404` | `204`, `404` | Aprobado |
| CIT-01 | Crear cita con cliente y servicios relacionados | `201`; reserva y cita persistidas | `201`; una reserva y una cita en SQLite | Aprobado |
| CIT-02 | Enviar fecha inválida o pasada | `422` | `422` | Aprobado |
| CIT-03 | Consultar cita inexistente | `404` | `404` | Aprobado |
| CIT-04 | Solicitar cita con profesional ocupado | `409` | `409` | Aprobado |
| CIT-05 | Simular fallo al guardar cita y comprobar rollback | `409`; cero reservas/citas huérfanas | `409`; cero reservas y cero citas | Aprobado |
| PRO-01 | Repetir asociación profesional-servicio en base | Rechazo por restricción única | `IntegrityError` | Aprobado |
| SEE-01 | Ejecutar seeder dos veces en base de prueba vacía | 2 registros conectados por cada entidad en ambos resultados | 2 clientes, servicios, profesionales, asociaciones, reservas y citas | Aprobado |
| OAS-01 | Consultar `/openapi.json`; revisar rutas, parámetros, DTO y códigos de respuesta | `200` y contrato documentado | `200`; esquema validado por prueba automatizada | Aprobado |

La suite también comprueba filtros y transiciones de estado de citas, reglas de agenda, validaciones de referencias, paginación y persistencia de cambios dentro de la base de prueba. Los casos detallados están en `tests/`.

## Matriz breve de requisitos

| Requisito | Estado | Evidencia |
|---|---|---|
| Fixtures aislados para las rutas | Probado | SQLite en memoria y claves foráneas en `tests/conftest.py`. |
| Seis o más casos reproducibles con resultados reales | Probado | Casos CLI, SER, CIT, PRO y SEE de esta matriz. |
| Seeder repetible sin registros manuales | Probado | `tests/test_seed.py` comprueba base inicialmente limpia y dos ejecuciones. |
| Contrato de Swagger con rutas, parámetros, DTO y códigos | Probado | `tests/test_openapi.py` valida `/openapi.json`. |
| CRUD HTTP de profesionales | Pendiente | Router no registrado; prueba marcada como omitida. |
| Migración desde PostgreSQL vacío y persistencia tras reinicio | Pendiente | Falta ejecutar en un entorno PostgreSQL integrado. |

## Qué demuestra y qué no

- El resultado demuestra comportamiento de la aplicación con SQLite temporal y sus fixtures; no prueba conexión PostgreSQL.
- No se ejecutó una migración contra una base PostgreSQL vacía ni se verificó persistencia al reiniciar contenedores en esta revisión.
- El CRUD HTTP de profesionales sigue pendiente de integración. Su caso automatizado está omitido explícitamente.
- Las dos ejecuciones consecutivas verifican que la suite se repite sin registros manuales; `tests/test_seed.py` además ejecuta el seeder dos veces sobre la misma base y verifica sus conteos.
- `tests/test_openapi.py` verifica el esquema que alimenta Swagger UI. La interfaz se sirve en `/docs` y el esquema en `/openapi.json`.
