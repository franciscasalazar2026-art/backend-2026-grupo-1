# Evidencias para la presentación — Isidora

## Qué desarrollé

Preparé fixtures de prueba con SQLite en memoria, casos automatizados para clientes, servicios, citas, agenda y seeder, y documentación para reproducirlos. En esta actualización añadí una prueba del contrato OpenAPI y descripciones de respuestas de error que faltaban para que aparezcan en Swagger.

## Evidencia reproducible

Desde la raíz del repositorio ejecuté dos veces consecutivas:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Salida de ambas ejecuciones:

```text
43 passed, 1 skipped
43 passed, 1 skipped
```

No hubo fallos. La prueba omitida es el CRUD HTTP de profesionales; sigue omitida porque `/profesionales` todavía no está registrado en la aplicación. En cada ejecución aparecen advertencias de compatibilidad de Pydantic y de `regex` en el router de servicios; no impidieron las pruebas.

## Demostración sugerida

1. Mostrar `tests/conftest.py`: base SQLite temporal, claves foráneas y fixture de datos relacionados.
2. Mostrar `tests/test_seed.py`: ejecuta el seeder dos veces y compara los conteos de clientes, servicios, profesionales, asignaciones, reservas y citas.
3. Mostrar `tests/test_openapi.py` y abrir `/docs`: la prueba consulta `/openapi.json` y verifica rutas, parámetros, DTO y respuestas documentadas.
4. Ejecutar `python -m pytest -q` para reproducir el resultado.
5. Aclarar el límite: esta evidencia usa SQLite; no acredita todavía una migración desde PostgreSQL vacío ni persistencia tras reiniciar Docker.

## Resultados frente a los requisitos

- Hay más de seis casos reproducibles y los códigos observados incluyen `201`, `200`, `404`, `409` y `422`.
- El rollback de una creación fallida deja cero reservas y cero citas en la base de prueba.
- El seeder produce dos registros relacionados por entidad y conserva los conteos al ejecutarse de nuevo.
- Una prueba queda omitida por falta de integración del router de profesionales; no se presenta como aprobada.
