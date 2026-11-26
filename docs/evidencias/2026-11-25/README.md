# Validación de Isidora Valverde del 25 de noviembre de 2026

Revisión ejecutada: `256c6bbc7f91be5d34cfe6793cfc4f7311c4a242`, en la rama `feature/isidora-arquitectura-evidencias`, basada en `main` `14b9af7`.

La ejecución terminó en **35,23 segundos**, con **107 aprobadas y cero fallos, errores, omisiones o advertencias**. La cobertura de líneas de `app` fue **87,44%**, con **1441 de 1648 líneas ejecutadas**, incluyendo el proceso Uvicorn de E2E. Se superó el umbral del 85% manteniendo en el cálculo los módulos legados con 0% y los mappers parcialmente cubiertos.

| Nivel | Aprobadas | Mínimo de la pauta |
| --- | ---: | ---: |
| Unitarias | 24 | 6 |
| Regresiones HTTP/SQLite | 65 | Complementarias |
| Integración PostgreSQL real | 14 | 6 |
| E2E HTTP externo | 4 | 3 |
| **Total** | **107** | |

| Archivo conservado | Contenido |
| --- | --- |
| [pytest.txt](pytest.txt) | Salida completa y cobertura por archivo. |
| [junit.xml](junit.xml) | Resultado y tiempo por caso. |
| [coverage.xml](coverage.xml) | Cobertura de cada línea instrumentada de `app`. |
| [resumen.json](resumen.json) | Revisión, versiones, conteos, opciones y SHA-256 de los tres reportes. |

Se normalizaron rutas de origen y se retiró el nombre del equipo de los reportes. Los saltos de línea se conservan como LF mediante `.gitattributes`, para que las huellas SHA-256 coincidan con los archivos publicados y al descargarlos en Windows o Linux. El contenido de las aserciones y los resultados se conserva. El entorno fue Windows, Python 3.13.15 y PostgreSQL 18.6 local; las versiones de las dependencias figuran en el resumen. Cada integración y cada E2E aplica Alembic a un esquema exclusivo y lo elimina al terminar.

Para repetir desde la raíz, sigue la preparación de [pruebas.md](../../../pruebas.md) y configura `TEST_POSTGRES_URL` hacia una base local exclusiva de pruebas.

```powershell
$env:E2E_STARTUP_TIMEOUT = '300'
if (-not $env:TEST_POSTGRES_URL) { throw 'Configura PostgreSQL local de pruebas' }
.\.venv\Scripts\python.exe -m pytest -q -W error --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=85 --junitxml=pytest-result.xml
```

Además, los cuatro E2E pasaron en una ejecución específica con `PGHOSTADDR=127.0.0.2` en el proceso padre y la base validada en `127.0.0.1`. La fixture fija el destino del proceso hijo y evita heredar una dirección diferente. Esa ejecución específica duró 8,75 segundos.

Ruff pasó para los seis archivos Python modificados con `--isolated --target-version py310 --select E4,E7,E9,F,I`. Este control acotado no acredita el pipeline ni el formato completo del repositorio.

Los resultados de [24 de noviembre](../2026-11-24/README.md) son históricos: 96 aprobadas y 87,38% en `a931df8`, con su comprobación Docker separada. El 88,26% citado anteriormente sigue sin un reporte de origen que permita reproducirlo. Esta ejecución de 107 pruebas se realizó contra PostgreSQL nativo y no dentro de Docker ni de Kubero.

La captura de Docker Desktop sigue pendiente: el intento del 25 encontró Windows bloqueado. Se restauró el stack complementario anterior, con su imagen `a931df8`; su estado no acredita un nuevo despliegue de `256c6bb`.

**Actualización del 26 de noviembre:** la [comprobación Docker y sus capturas](../2026-11-26/README.md) resuelven esa captura pendiente y acreditan la operación complementaria de `256c6bb`, con la misma revisión del código de esta suite. Este informe conserva el entorno y los resultados originales del 25.

La [lista de cierre de Isidora](../../cierre-isidora.md), la [retroalimentación](../../retroalimentacion.md) y la [matriz de la rúbrica](../../matriz-evidencias-rubrica.md) conectan los resultados con cada requisito y sus límites.
