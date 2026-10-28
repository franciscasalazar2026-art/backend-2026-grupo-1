# Pruebas automatizadas del backend

## Ejecución reproducible

Las pruebas usan una base SQLite temporal en memoria, crean todas las tablas ORM y activan las claves foráneas. No leen credenciales locales, no necesitan PostgreSQL y eliminan la base al cerrar cada caso.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest -q
```

Los datos de prueba se crean desde fixtures por caso. El seeder reutilizable para un PostgreSQL de desarrollo se ejecuta después de `alembic upgrade head` con `python scripts/seed.py`.

## Casos ejecutados

Última ejecución local: Python 3.13, `python -m pytest -q` — **15 aprobados, 6 omitidos**. Los omitidos corresponden a rutas/reglas aún ausentes de `main`; se explicitan en las pruebas y se deben habilitar cuando los respectivos PR estén integrados.

| ID | Área | Entrada y comprobación | Resultado observado | Estado |
| --- | --- | --- | --- | --- |
| CLI-01 | Clientes | Crear cliente y consultarlo por ID | `POST 201`, `GET 200`, email conservado | Aprobado |
| CLI-02 | Clientes | Repetir correo | `409` | Aprobado |
| CLI-03 | Clientes | Correo inválido | `422` | Aprobado |
| CLI-04 | Clientes | ID inexistente | `404` | Aprobado |
| CLI-05 | Clientes | Listar con límite y desplazamiento | `200`, 3 totales y 2 elementos de página | Aprobado |
| SER-01 | Servicios | Crear y listar | `POST 201`, `GET 200` | Aprobado |
| SER-02 | Servicios | Precio negativo o duración cero | `422` en ambos casos | Aprobado |
| SER-03 | Servicios | Consultar ID inexistente | Preparado; la ruta `GET /servicios/{servicio_id}` no está en `main` | Omitido |
| SER-04 | Servicios | Actualizar y consultar ID inexistente | Preparado; `PUT /servicios/{servicio_id}` no está en `main` | Omitido |
| SER-05 | Servicios | Eliminar e ID inexistente | Preparado; `DELETE /servicios/{servicio_id}` no está en `main` | Omitido |
| PRO-01 | Profesionales | Repetir asociación profesional-servicio | Restricción única rechaza el duplicado | Aprobado |
| PRO-02 | Profesionales | CRUD y asignación por HTTP | Preparado; el router `/profesionales` no está en `main` | Omitido |
| CIT-01 | Citas | Crear cita con cliente, profesional, servicio y relación existente | `201`; se guardan una reserva y una cita | Aprobado |
| CIT-02 | Citas | Fecha con formato inválido | `422` | Aprobado |
| CIT-03 | Citas | ID inexistente | `404` | Aprobado |
| CIT-04 | Citas | Filtrar estado, ordenar y paginar | `200`, metadatos y elemento esperado | Aprobado |
| CIT-05 | Agenda | Fecha pasada | Preparado; rechazo aún no implementado en `main` | Omitido |
| CIT-06 | Agenda | Dos citas superpuestas para la profesional | Preparado; regla de traslape aún no implementada en `main` | Omitido |
| CIT-07 | Transacción | Simular fallo al insertar la cita después de crear reserva | `409`; rollback deja 0 reservas y 0 citas | Aprobado |
| SEE-01 | Seeder | Ejecutarlo dos veces sobre base vacía | Mantiene 2 clientes, servicios, profesionales, asociaciones, reservas y citas | Aprobado |

## Alcance y pendientes

- Las pruebas ejercitan las rutas integradas en la rama actual y las relaciones con SQLite; no demuestran el comportamiento real de PostgreSQL.
- Docker, la migración Alembic desde una base PostgreSQL vacía y la persistencia después de reiniciar el servidor todavía requieren una configuración PostgreSQL disponible.
- Los casos omitidos están identificados con `pytest.mark.skip` y explican la ruta o regla faltante. No cuentan como aprobados.
- La prueba de rollback inyecta un error de integridad durante la segunda escritura de `/citas` y comprueba que no quede una reserva huérfana.
- El seeder usa correos `seed.*@example.test` y motivos con prefijo `[SEED]` para identificar sus datos; no elimina otros registros.
