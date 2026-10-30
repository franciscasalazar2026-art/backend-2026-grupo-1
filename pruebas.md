# Pruebas automatizadas del backend

## Ejecución reproducible

Las pruebas utilizan una base de datos SQLite temporal en memoria. Se crean las tablas ORM y se activan las claves foráneas. No requieren credenciales locales ni conexión a PostgreSQL. La base de datos se elimina al finalizar cada caso.

Para preparar el entorno y ejecutar las pruebas:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest -v
```

Los datos de prueba se crean mediante fixtures. El seeder reutilizable para PostgreSQL se ejecuta después de aplicar las migraciones con `alembic upgrade head`, mediante `python scripts/seed.py`.

## Resultados de la última ejecución

Última ejecución local: Python 3.13, `python -m pytest -v`.

**Resultado: 36 aprobados, 3 omitidos y 0 fallidos.**

| Área | Pruebas aprobadas | Pruebas omitidas |
|---|---:|---:|
| Citas | 24 | 0 |
| Clientes | 5 | 0 |
| Profesionales | 1 | 1 |
| Servicios | 5 | 2 |
| Seeder | 1 | 0 |
| **Total** | **36** | **3** |

## Casos de prueba de citas

| ID | Área | Entrada y comprobación | Resultado |
|---|---|---|---|
| CIT-01 | Citas | Crear cita y comprobar reserva y cita en base de datos | Aprobado |
| CIT-02 | Citas | Fecha con formato inválido | Aprobado |
| CIT-03 | Citas | Consultar cita inexistente | Aprobado |
| CIT-04 | Citas | Filtrar, ordenar y paginar citas | Aprobado |
| CIT-05 | Agenda | Rechazar fecha pasada | Aprobado |
| CIT-06 | Agenda | Rechazar citas con horarios superpuestos | Aprobado |
| CIT-07 | Transacciones | Simular fallo durante la creación y comprobar rollback | Aprobado |
| CIT-08 | Estados | Transiciones permitidas desde pendiente | Aprobado |
| CIT-09 | Estados | Transición de confirmada a completada | Aprobado |
| CIT-10 | Estados | Rechazar transiciones no permitidas | Aprobado |
| CIT-11 | Agenda | Rechazar actualización a fecha pasada | Aprobado |
| CIT-12 | CRUD | Consultar una cita existente | Aprobado |
| CIT-13 | CRUD | Actualizar motivo de una cita | Aprobado |
| CIT-14 | CRUD | Eliminar una cita existente | Aprobado |
| CIT-15 | CRUD | Eliminar una cita inexistente | Aprobado |
| CIT-16 | Validaciones | Rechazar servicio inexistente | Aprobado |
| CIT-17 | Validaciones | Rechazar profesional inexistente | Aprobado |
| CIT-18 | Validaciones | Rechazar profesional sin asignación al servicio | Aprobado |
| CIT-19 | Validaciones | Rechazar cliente inactivo | Aprobado |
| CIT-20 | Validaciones | Rechazar servicio inactivo | Aprobado |
| CIT-21 | Validaciones | Rechazar profesional inactivo | Aprobado |
| CIT-22 | Agenda | Detectar solapamiento parcial de horarios | Aprobado |

## Otras áreas verificadas

- **Clientes:** creación, consulta, correo duplicado, formato de correo y paginación.
- **Profesionales:** rechazo de asociaciones duplicadas entre profesionales y servicios.
- **Servicios:** creación, listado, validación de precio y duración, y consulta de identificadores inexistentes.
- **Seeder:** ejecución reproducible y creación de registros relacionados.

## Pruebas omitidas

Las siguientes pruebas están preparadas, pero se mantienen omitidas porque las operaciones correspondientes todavía no están integradas:

| Área | Prueba omitida | Motivo |
|---|---|---|
| Profesionales | CRUD y asignación por HTTP | Router `/profesionales` pendiente de integración |
| Servicios | Actualizar servicio | PUT `/servicios/{servicio_id}` pendiente de integración |
| Servicios | Eliminar servicio | DELETE `/servicios/{servicio_id}` pendiente de integración |

Las pruebas omitidas no se contabilizan como aprobadas.

## Reglas de negocio implementadas en citas

Actualmente se encuentran implementadas y verificadas mediante pruebas automatizadas:

- Validación de existencia y actividad del cliente.
- Validación de existencia y actividad del servicio.
- Validación de existencia y actividad del profesional.
- Validación de la asociación entre profesional y servicio.
- Rechazo de fechas pasadas.
- Prevención de conflictos y solapamientos de horarios.
- Control de transiciones permitidas entre estados.
- Actualización de fecha y motivo de la cita.
- Manejo de transacciones y rollback ante errores.

## Alcance y limitaciones

- Las pruebas automatizadas utilizan SQLite temporal y verifican las rutas integradas en la aplicación.
- Los resultados no demuestran por sí solos el funcionamiento de la conexión real con PostgreSQL.
- La migración Alembic desde una base PostgreSQL vacía, la persistencia después de reiniciar el servidor y la configuración Docker/Compose requieren verificaciones adicionales.
- El router de profesionales y las operaciones PUT y DELETE de servicios continúan pendientes de integración.
- La prueba de rollback comprueba que un fallo durante la creación de la cita no deje una reserva huérfana.

Los resultados documentados corresponden a la última ejecución local indicada y deben actualizarse cuando se incorporen nuevas funcionalidades o pruebas.