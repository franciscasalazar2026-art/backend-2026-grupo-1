# Informe de arquitectura y validación de las tareas 3 y 4

> Registro de la revisión del 24 de noviembre. La ampliación del 25, contrastada con el plan de Isidora, está en la [lista de cierre](cierre-isidora.md), con [107 aprobadas y 87,44% de cobertura](evidencias/2026-11-25/README.md). Los datos siguientes identifican su propia revisión histórica.

**Responsable:** Isidora Valverde

**Fecha:** 24 de noviembre de 2026

La revisión parte de `main` `14b9af7`. La ejecución consolidada corresponde al commit `a931df826436d40a1976b2e306f361fc74f2a0aa` y terminó con **96 pruebas aprobadas, cero fallidas, cero errores, cero omisiones y cero advertencias**. La cobertura de líneas de `app` fue **87,38%**, sobre el mínimo de 85%. El [resumen verificable](evidencias/2026-11-24/resumen.json) identifica revisión, entorno, conteos y huellas SHA-256 de los reportes.

## Tarea 3 Revisión de arquitectura

| Elemento revisado | Conclusión | Corrección propuesta |
| --- | --- | --- |
| `app/schemas/schemas.py` | Es un contrato anterior que solo es importado por el repositorio legado. Los puntos de entrada activos utilizan los DTO de presentación. | Retirar en un cambio acotado junto al repositorio en memoria, tras confirmar consumidores externos y ejecutar las regresiones y OpenAPI. |
| `app/repositories/database.py` | Mantiene listas de demostración sin consumidores en las fuentes vigentes. La conexión activa es SQLAlchemy/PostgreSQL en infraestructura. | Retirar el módulo y sus cachés versionadas mediante revisión. |
| Mappers de clientes, profesionales y servicios | Los tres `a_entidad` tienen 14 llamadas directas y devuelven entidades de dominio en las comprobaciones ejecutadas. Sus tres `a_modelo` solo aparecen como definiciones. | Conservar la conversión ORM → dominio. Revisar y retirar los inversos sin uso si el equipo confirma que carecen de consumidores externos. |
| Dependencias entre capas | `AuthServicio` importa adaptadores concretos. El puerto de profesionales permite devolver un `ServicioORM`. Hay reglas de agenda dentro del repositorio. | Introducir puertos de autenticación, correo y seguridad, devolver entidades por los puertos y trasladar reglas puras al dominio en cambios separados con regresiones. |

La [revisión detallada de arquitectura](revision-arquitectura.md) contiene imports, líneas de código, comprobaciones de ejecución, diagrama de capas y riesgos de cada propuesta. El diagnóstico utiliza referencias y recorridos reales además del reporte de cobertura. Esta entrega conserva los módulos identificados para que su retiro sea revisable por el equipo.

## Tarea 4 Pruebas y cobertura

| Nivel | Aprobadas | Qué comprueba |
| --- | ---: | --- |
| Unitarias | 21 | Política de contraseña, hash, firma y propósito JWT, permisos, servicio aislado y buzón local. |
| Regresiones con SQLite | 61 | CRUD con roles, validaciones, profesionales, agenda, seeder repetible, relaciones y OpenAPI. |
| Integración PostgreSQL | 11 | Migraciones desde un esquema vacío, unicidad, claves foráneas, persistencia de refresh, consumo concurrente y rollback real. |
| E2E por HTTP | 3 | Uvicorn en otro proceso, acceso y negocio protegido, recuperación y revocación, permisos 401/403/201. |
| **Total** | **96** | **Sin fallos, errores u omisiones.** |

El entorno fue Windows, Python 3.13.15 y PostgreSQL 18.6. Las versiones de FastAPI, Starlette, SQLAlchemy, pytest y cobertura están en [resumen.json](evidencias/2026-11-24/resumen.json). Cada integración y E2E prepara su propio esquema mediante Alembic y lo elimina al finalizar. La cobertura incorpora el proceso HTTP de Uvicorn.

La cifra de **88,26%** indicada en la tarea se conserva como antecedente. El reporte reproducido en esta revisión mide **1440 líneas ejecutadas de 1648 ejecutables**, equivalente a **87,38%**. La comparación exacta requiere el commit, el entorno y el reporte de la medición anterior. Los módulos legados con 0% y los inversos de mappers sin ejecutar permanecen incluidos en el cálculo.

Para repetir la ejecución desde el repositorio, prepara una base local exclusiva de pruebas según [pruebas.md](../pruebas.md) y ejecuta:

```powershell
$env:E2E_STARTUP_TIMEOUT = '300'
if (-not $env:TEST_POSTGRES_URL) { throw 'Configura la URL local de PostgreSQL de pruebas' }
& .\.venv\Scripts\python.exe -m pytest -q -W error --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=85 --junitxml=pytest-result.xml
```

Los archivos publicados son [salida de pytest](evidencias/2026-11-24/pytest.txt), [JUnit](evidencias/2026-11-24/junit.xml) y [cobertura por archivo](evidencias/2026-11-24/coverage.xml). Sus rutas de origen se normalizaron para evitar referencias al equipo local.

## Advertencias y arranque E2E

Las cinco advertencias de Starlette procedían de leer `HTTP_422_UNPROCESSABLE_ENTITY` en el manejador global de validación. Se usa ahora `HTTP_422_UNPROCESSABLE_CONTENT`, con el valor numérico 422 como respaldo para versiones anteriores. Se mantiene el estado HTTP y el cuerpo de error. Los cinco casos afectados y la batería completa pasaron con `-W error`.

La primera ejecución durante el arranque de Docker terminó con 94 casos aprobados, dos errores de preparación E2E por el límite de 20 segundos y cinco advertencias. Sus logs de Uvicorn mostraron arranque y cierre normales. Se añadió `E2E_STARTUP_TIMEOUT`, con 60 segundos predeterminados y valores mayores que cero y hasta 300. Conserva el sondeo breve, el fallo inmediato si el proceso termina y la ubicación del log. La ejecución final utilizó 300 segundos de margen y terminó en 124,19 segundos para toda la batería.

## Capturas y operación local

El [índice de evidencias](evidencias/2026-11-24/README.md) conserva las capturas de Swagger, su respuesta HTTP 200 y las once tablas PostgreSQL. La imagen de Docker Desktop queda pendiente: Escape interrumpió el control de la interfaz antes de capturarla.

La [comprobación de operación Docker](evidencias/2026-11-24/docker-operacion.json) registra los tres servicios activos, la migración `c4d987ee6f20`, el digest y la revisión `a931df8` de la imagen. Se construyó desde un archivo limpio de ese commit. Tras recrear únicamente la API, los conteos e identificadores de los datos ficticios permanecieron iguales; la base, el visor y el volumen conservaron sus identificadores.

Esta comprobación usa Python 3.10.22 y PostgreSQL 15.20 en un [Compose complementario](evidencias/2026-11-24/compose.evidencias.yml), con secretos locales y un visor Adminer. Las 96 pruebas y su cobertura corresponden al entorno nativo descrito anteriormente. El Compose principal del proyecto sigue requiriendo las mejoras señaladas en C3 de la matriz.

## Correspondencia con la rúbrica

La [matriz de evidencias](matriz-evidencias-rubrica.md) contiene los once criterios de código y los nueve de presentación y defensa. Las pruebas de los tres niveles y el umbral de cobertura quedan verificadas en el entorno descrito.

El cierre general requiere completar la trazabilidad de las observaciones originales y P1–P7, revisar la protección de las operaciones de citas y profesionales, limitar solicitudes repetidas de recuperación y verificar el transporte de refresh si se consume desde navegador. También faltan evidencias de CI verde y fallo bloqueado, la revisión desplegada con HTTPS en Kubero y el ensayo de presentación. La matriz vincula cada pendiente con la comprobación que permitiría cerrarlo.
