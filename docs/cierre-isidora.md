# Cierre de la parte de Isidora Valverde

Revisión del 25 de noviembre de 2026, actualizada con evidencias operacionales del 26, de la sección 3 de *Plan de trabajo Backend.pdf*, contrastada con 5.5–5.7 y las condiciones colaborativas de *Proyecto_Backend_Entrega_Final.docx (1).pdf*. La revisión corresponde a calidad, pruebas y documentación. Los documentos aportan los criterios; el estado se determina con el código y las comprobaciones ejecutadas.

## Requisitos asignados y resultado

| Tarea de Isidora | Resultado comprobado | Evidencia |
| --- | --- | --- |
| Adaptar pruebas a JWT y roles | Fixtures con cuentas y tokens reales; regresiones de negocio autenticadas y comparación 401/403/201 en la misma operación. | [Fixtures](../tests/conftest.py), [regresiones](../tests) y [permisos E2E](../tests/e2e/test_auth_e2e.py). |
| Al menos seis unitarias | 24 aprobadas: política, hash, JWT, permisos, servicio aislado y correo. Se incorporaron bloqueo en el quinto fallo, fin del bloqueo y cuenta inactiva. | [Unitarias](../tests/unit), [JUnit](evidencias/2026-11-25/junit.xml). |
| Al menos seis integraciones reales | 14 aprobadas sobre PostgreSQL, con Alembic y esquemas aislados. Incluyen unicidad, relaciones, refresh, recuperación, rollback y concurrencia. | [Integración](../tests/integration), [preparación](../tests/support/postgres.py). |
| Tres escenarios E2E completos | Cuatro aprobados por HTTP contra Uvicorn y PostgreSQL reales. Cubren acceso y negocio, registro público, recuperación y permisos. | [Escenarios](../tests/e2e/test_auth_e2e.py), [servidor](../tests/e2e/conftest.py). |
| Cobertura mínima del 85% | 87,44% de líneas de `app`, incluyendo el subproceso HTTP; 107 aprobadas en total y cero omisiones o advertencias. | [Reportes del 25 de noviembre](evidencias/2026-11-25/README.md). |
| Consolidar retroalimentación | Tabla con ID, procedencia, cambio, archivo/commit, comprobación y estado. Los hallazgos propios se distinguen de comentarios docentes. | [Registro R-01 y T-01–T-13](retroalimentacion.md). |
| README y guía de pruebas | Preparación desde cero, comandos por nivel y conjunto, flujo JWT, recuperación, cuentas demo funcionales y OpenAPI. | [README](../README.md), [pruebas.md](../pruebas.md). |
| Capturas y operación local | Swagger y salud 200, tres contenedores activos, once tablas PostgreSQL y datos conservados al recrear solo la API. | [Capturas y registro del 26 de noviembre](evidencias/2026-11-26/README.md). |

El registro público mantiene el rol cliente aunque se solicite admin. Como esa cuenta no debe crear clientes, el escenario adicional prepara el recurso por HTTP con personal autorizado y comprueba su consulta autenticada, el rechazo de escritura, logout y renovación rechazada. El E2E original conserva creación y consulta con personal preparado en la base aislada, permitido por 5.7.

Recuperación comprueba dos sesiones previas invalidadas, contraseña anterior rechazada, JWT reutilizado y pendiente rechazados y acceso nuevo válido. Enviar el ID de otra cuenta no cambia la cuenta objetivo determinada por el JWT: la otra cuenta conserva su contraseña y su sesión.

## Commits nuevos de esta revisión

La identidad Git es **Isidora Valverde**. Después de `303e039`, esta ampliación aporta más de los cinco commits nuevos significativos exigidos; los tres commits de arquitectura y evidencias del 24 se conservan aparte.

| Commit | Aporte |
| --- | --- |
| `0733098` | Unitarias de bloqueo, desbloqueo y cuenta inactiva. |
| `b64e640` | Persistencia del bloqueo, correo único normalizado y concurrencia con dos JWT distintos. |
| `7507e4d` | Registro HTTP sin autoasignación de privilegios y recuperación sin cambiar otra cuenta. |
| `5c0b1f3` | Login real de cuentas demo y documentación de su preparación. |
| `8f5bf94` | Destino PostgreSQL local explícito para el proceso E2E. |
| `256c6bb` | Actualización del correo demo antiguo conservando la cuenta y pruebas de colisiones. |
| `4e7d73c` | Consolidación de la ejecución completa, la lista de cierre y la matriz actualizada. |
| Commit de las capturas del 26 | Capturas actuales de Swagger, Docker y PostgreSQL, registro de persistencia y configuración reproducible sin secretos. |

El [PR 26](https://github.com/franciscasalazar2026-art/backend-2026-grupo-1/pull/26) concentra estos aportes hacia `main`; su estado en GitHub acredita la integración cuando figure como fusionado. El número de commits en una rama no acredita por sí solo los aportes de las demás integrantes.

## Preparar la explicación de las pruebas

1. Abre [pruebas.md](../pruebas.md), configura una base de pruebas local y ejecuta un nivel. Explica que SQLite es regresión y que integración usa PostgreSQL con migraciones reales.
2. En `test_auth_servicio.py`, muestra la prueba del quinto fallo. El reloj está fijado y el repositorio es un doble; no se espera quince minutos ni se consulta una base real.
3. En `test_postgres_auth.py`, muestra la lectura del bloqueo desde otra sesión y el caso concurrente. Explica la aserción que distingue una sola contraseña ganadora y su persistencia.
4. En E2E, sigue registro/login, cabecera Bearer, operación, logout y rechazo de refresh. Explica por qué las cuentas públicas conservan cliente y cómo se prepara el personal de pruebas.
5. Abre JUnit y cobertura del commit validado. Las capturas de Swagger muestran una interfaz disponible; los escenarios automatizados completos se acreditan mediante las pruebas HTTP.

Estos pasos son material de preparación. La presentación sorteada, el tiempo de exposición y la comprensión de todo el equipo requieren ensayo y defensa; esta revisión no los certifica.

## Pendientes del cierre compartido

| Pendiente | Área del plan / alcance |
| --- | --- |
| Comprobar la integración de todos los PR, los cinco aportes de cada integrante y crear `v1.0` en el commit final integrado | Todas y coordinación. El PR individual está enlazado arriba; no se etiqueta una versión final mientras el cierre del equipo siga pendiente. |
| Adjuntar observaciones originales de I/II y relacionarlas con los cambios | Coordinación y responsables de cada observación. El registro distingue lo que sí se pudo reproducir. |
| Proteger operaciones privadas y administrativas de citas y profesionales | Francisca Alvarado. La matriz conserva el hallazgo; los tests nuevos no sustituyen esa implementación. |
| Compose principal con visor y variables; pipeline, fallo bloqueado, imagen y Kubero con HTTPS | Francisca Salazar. Los reportes locales no acreditan CI ni despliegue institucional. |
| Límite de solicitudes repetidas de recuperación y transporte de refresh para navegador | Seguridad e integración. Son partes todavía parciales de C5/C6; se conserva la evidencia de lo ya probado. |
| Ensayo y presentación de hasta quince diapositivas, diez minutos y defensa | Todas. Usar cuentas ficticias y ocultar tokens al mostrar flujos. |

El plan describe una mezcla de tipos de caracteres para contraseñas; la pauta de 5.5 y la implementación revisadas exigen mínimo doce caracteres. Se documenta esa diferencia para acordar el contrato; las contraseñas demo cumplen ambas descripciones.
