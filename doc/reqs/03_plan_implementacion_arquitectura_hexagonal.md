# PLAN-01 · Implementación incremental de REQS-01

> **Estado:** Completada (Fases 0 a 10). Fase 10 cerró el ciclo: `--mvc` retirado, módulos heredados de 2 capas eliminados, `users` regenerado íntegramente con el generador como módulo de referencia, CI y documentación sincronizadas.
> **Alcance:** Implementar REQS-01 con GenCLI v2: `--hex` crea el núcleo y cada `--uc-*` añade una capacidad vertical.
> **Estimación total:** 18 días hábiles de desarrollo efectivo para una persona senior, más 1.5 a 2 días de contingencia.
> **Restricción del plan:** Ninguna fase supera 2 días hábiles.
> **Excluido:** REQS-02 (API Keys y hardening de seguridad) inicia después del cierre de este plan.

---

## 1. Principios de ejecución

1. **El generador es el producto:** no se acepta una modificación manual en `users` o `products` que GenCLI no pueda reproducir.
2. **Vertical antes que masivo:** se completa y valida `--uc-list` antes de crear los demás comandos.
3. **Idempotencia desde el inicio:** repetir cualquier `--uc-*` no duplica imports, métodos, rutas ni registros de router.
4. **Persistencia eficiente por defecto:** paginación cursor/keyset y búsqueda dinámica validada se implementan antes de expandir el CRUD.
5. **Una fase, un resultado verificable:** al final de cada fase existe código, templates o pruebas revisables y una condición clara de salida.

## 2. Decisiones de inicio

| ID | Decisión | Resolución para este plan |
|---|---|---|
| D-01 | Límite transaccional | Use cases llaman `uow.commit()` explícitamente al terminar una operación de escritura; repositorios solo hacen `flush()`. Se corrige la contradicción actual de REQS-01 antes de programar. |
| D-02 | `isPhisical` → `is_physical` | Cambio interno obligatorio. Los módulos nuevos exponen solo `is_physical`; no se genera alias Pydantic. La compatibilidad, si un consumidor heredado la requiere, permanece fuera del generador. |
| D-03 | Edición de archivos existentes | Scripts Python en `.gen_cli/scripts/`, con marcadores `gencli:*`, edición determinista, validación `ast.parse` e idempotencia. |
| D-04 | Rutas de listado coexistentes | `GET /` para `--uc-list`; `GET /paginated` para `--uc-list-paginated`; `POST /find-by` para `--uc-find-by`. |

## 3. Fases de trabajo

### Fase 0 — Línea base y contrato actual

**Duración:** 0.5 día
**Estado:** Completada.

**Actividades:**

- Ejecutar `poe lint`, `poe typecheck`, `poe test` y e2e opt-in; registrar los resultados iniciales.
- Inventariar rutas, payloads, respuestas y códigos HTTP de `users` y `products`.
- Verificar la sintaxis de los templates actuales y el comportamiento de `gen --mvc` como referencia de regresión.
- Crear una matriz requisito → template/script/prueba.

**Entregables:**

- Bitácora de baseline.
- Contrato HTTP de referencia.
- Matriz de trazabilidad inicial.

**Salida:** Se puede detectar una regresión HTTP, de generación o de calidad en fases posteriores.

### Fase 1 — Estabilización y shared kernel

**Duración:** 1.5 días
**Estado:** Completada.

**Actividades:**

- Eliminar el import inexistente de `src.modules.cosas` y lógica muerta en entidades.
- Normalizar `__init__.py`, nombre de README y dependencias de desarrollo duplicadas.
- Crear `shared/domain/errors.py` y `shared/domain/unit_of_work.py`.
- Implementar UoW sobre `AsyncSession`, con `flush()` en repositorios y `commit()` explícito en use cases.
- Añadir handlers globales RFC 9457 (`problem+json`) para errores de dominio.
- Añadir test de arquitectura que prohíba FastAPI, SQLAlchemy y Pydantic dentro de `domain/`.

**Entregables:**

- Shared kernel mínimo y pruebas unitarias de handlers/imports.
- ADR o actualización de REQS-01 que formalice D-01.

**Salida:** App arrancable; lint, typecheck y pruebas base en verde; errores de dominio mapeados sin inspeccionar strings.

### Fase 2 — Comando base `--hex`

**Duración:** 1.5 días
**Estado:** Completada.

**Actividades:**

- Crear la arquitectura `--hex` en `arq.json`.
- Crear templates del núcleo: entidad, puerto de repositorio, excepciones, modelo, adaptador vacío, dependencies, `__init__.py` y carpetas.
- Incluir marcadores `gencli:*` en todos los archivos que recibirán extensiones posteriores.
- Generar un módulo temporal, comprobar árbol de archivos, importar el paquete y validar con Ruff/MyPy.
- Documentar la sintaxis de `--hex` y el estado inicial sin router en `main.py`.

**Entregables:**

- Entrada `--hex` funcional en `arq.json`.
- Templates base bajo `.gen_cli/templates/hex/`.
- Módulo temporal generado y validado.

**Salida:** `gen --hex User "nombre:str,email:str"` genera un módulo importable, sin casos de uso ni exposición HTTP.

### Fase 3 — Infraestructura de hooks y mutaciones idempotentes

**Duración:** 1.5 días
**Estado:** Completada.

**Actividades:**

- Crear librería interna común en `.gen_cli/scripts/` para lectura, inserción en marcadores, deduplicación y escritura atómica.
- Implementar validación con `ast.parse` antes de persistir cada mutación Python.
- Definir convenciones de bloque para imports, métodos de puertos, métodos de adaptadores, providers, rutas e `include_router`.
- Implementar script de registro de router en `main.py`, sin duplicados y sin modificar nada si el marcador no existe.
- Crear fixtures de archivos válidos, ya modificados, sin marcador y con sintaxis inválida.

**Entregables:**

- Utilidades reutilizables de scripts GenCLI.
- Tests unitarios de idempotencia, fallos seguros y parseo AST.
- Script base de registro de router.

**Salida:** Un script se puede ejecutar dos veces contra los fixtures sin diferencias en la segunda ejecución; un fallo no deja archivos parcialmente modificados.

### Fase 4 — `--uc-list` vertical de referencia

**Duración:** 1.5 días
**Estado:** Completada a nivel de generador y validada en un proyecto aislado con GenCLI v2.1. La migración del módulo heredado `users` se pospone para evitar mantener rutas CRUD mixtas mientras faltan `--uc-create`, `--uc-get`, `--uc-update` y `--uc-delete`.

**Actividades:**

- Crear templates de `--uc-list`: use case, controller, schemas, ruta `GET /` y tests.
- Crear hook único que añade `list` al puerto, al adaptador SQLAlchemy, al provider y al router existente.
- Registrar el router del módulo en `main.py` solo si aún no existe.
- Aplicar el comando al módulo `users` generado o migrado con `--hex`.
- Crear fake repository y pruebas unitarias sin PostgreSQL; validar el e2e del endpoint.

**Entregables:**

- Entrada `--uc-list` y script `register_uc_list.py`.
- Módulo `users` con listado simple limitado y ruta funcional.
- Tests del generador, unitarios y e2e.

**Salida:** Repetir `gen --uc-list User ...` no duplica nada y `GET /api/v1/users/` respeta el límite máximo del servidor.

### Fase 5 — `--uc-list-paginated` con cursor/keyset

**Duración:** 2 días
**Estado:** Completada.

**Actividades:**

- Definir cursor opaco, firmado/codificado y validado; definir orden estable e índices requeridos.
- Crear templates de use case, DTOs, controller, ruta `GET /paginated` y tests.
- Extender puerto y adaptador con `list_paginated(limit, cursor)` mediante keyset, sin `OFFSET`.
- Crear hook idempotente para contratos, provider y ruta.
- Probar primera página, páginas siguientes, final de colección, cursor inválido, límite mínimo/máximo y orden estable.

**Entregables:**

- Entrada `--uc-list-paginated` y script asociado.
- Contrato `items`, `next_cursor`, `has_next`, `limit`.
- Índices/migración documentados para la ordenación seleccionada.

**Salida:** La inspección de la query y los tests prueban que no existe `OFFSET`; la paginación es estable bajo colecciones grandes.

### Fase 6 — `--uc-find-by` dinámico y seguro

**Duración:** 2 días
**Estado:** Completada.
**Estado:** Completada a nivel de generador y validada en un proyecto aislado con GenCLI.

**Actividades:**

- Definir `FindByCriteria`, `FindByResult` y el mapa de campos buscables por entidad.
- Definir allowlist inicial de operadores: `equals`, `contains`, `starts_with`; validar tipos antes de persistencia.
- Crear templates de caso de uso, payload, controller, `POST /find-by`, respuesta limitada/paginada y pruebas.
- Extender puerto y adaptador con consultas ORM parametrizadas; prohibir interpolación de SQL recibido.
- Integrar `pagination: bool | None`: false/ausente devuelve resultado limitado; true usa el mismo cursor/keyset de Fase 5.
- Cubrir campos/operadores no permitidos, valores inválidos, búsqueda con y sin paginación.

**Entregables:**

- Entrada `--uc-find-by` y script asociado.
- Endpoint genérico de búsqueda para `users`.
- Tests de allowlists, validación de tipos, límites y paginación.

**Salida:** El cliente puede elegir paginar en cada petición; no puede consultar columnas internas ni ejecutar operadores fuera de la allowlist.

### Fase 7 — `--uc-create` y `--uc-get`

**Duración:** 2 días
**Estado:** Completada a nivel de generador y validada con hooks idempotentes y composicion aislada.

**Actividades:**

- Crear templates, hooks y tests para creación (`POST /`) y consulta individual (`GET /{id}`).
- Añadir métodos `save` y `find_by_id` al puerto/adaptador mediante scripts idempotentes.
- Implementar excepciones de dominio para conflicto y no encontrado.
- Verificar una única transacción por operación de escritura y mapping HTTP centralizado.

**Entregables:**

- Entradas `--uc-create` y `--uc-get`.
- Módulo `users` con create/get generado por GenCLI.
- Pruebas unitarias y e2e de ambos comandos.

**Salida:** Las rutas devuelven 201, 404 y 409 según corresponda, sin que controllers conozcan SQLAlchemy.

### Fase 8 — `--uc-update` y `--uc-delete`

**Duración:** 2 días
**Estado:** Completada a nivel de generador. `PUT /{id}` reemplaza el estado completo del agregado; `DELETE /{id}` realiza eliminación lógica en UTC. Ambos hooks son idempotentes, atómicos y componen con las rutas de colección previas.

**Actividades:**

- Crear templates, hooks y tests para actualización (`PUT`, reemplazo completo) y eliminación lógica (`DELETE /{id}`).
- Añadir operaciones necesarias al puerto y adaptador.
- Verificar rollback ante errores de integridad y que registros eliminados no aparezcan en list/find-by.
- Revisar consistencia de soft delete, UTC y UUIDv7.

**Entregables:**

- Entradas `--uc-update` y `--uc-delete`.
- CRUD completo de `users`, reproducible exclusivamente mediante comandos incrementales.
- Suite de regresión de soft delete.

**Salida:** Todos los `--uc-*` definidos funcionan de forma independiente y repetible sobre el mismo módulo.

### Fase 9 — Validación cruzada con `products`

**Duración:** 2 días
**Estado:** Completada. La regresión ejecuta `./gen` en un proyecto temporal aislado para `Product` con `name:str,user:UUID,is_physical:bool`, seguido de todos los comandos `--uc-*`. Verifica composición idempotente, tipos y mapeos, orden de rutas, filtros de eliminación lógica y ausencia de `OFFSET`.

**Actividades:**

- Aplicar `--hex` y los comandos de caso de uso a un módulo Product aislado, sin editar archivos estructurales a mano ni modificar el módulo heredado `src/modules/products`.
- Resolver D-02 para `is_physical` y actualizar tests/contrato de acuerdo con la decisión.
- Verificar que tipos UUID, booleanos y campos de ownership funcionan en generación, búsqueda y paginación.
- Corregir defectos de generalización en templates y scripts descubiertos con el segundo módulo.

**Entregables:**

- Smoke test aislado de `Product` con el mismo flujo GenCLI.
- Correcciones de plantillas genéricas y pruebas de regresión.

**Compatibilidad:** El generador nuevo usa `is_physical` tanto internamente como en su API. No genera el alias heredado `isPhisical`: conservarlo propagaría una errata a módulos nuevos. El módulo legado `src/modules/products` no se modifica en esta fase; cualquier adaptación de compatibilidad queda limitada a consumidores heredados fuera del generador.

**Salida:** Dos módulos con propiedades distintas son generados mediante exactamente los mismos comandos, sin parches manuales de arquitectura.

### Fase 10 — Calidad, documentación y cierre

**Duración:** 1.5 días
**Estado:** Completada. `--mvc` fue retirado de `arq.json` junto con sus templates; los módulos heredados `users` y `products` (2 capas) y la suite e2e heredada se eliminaron; `users` se regeneró exclusivamente con `--hex` + los siete `--uc-*` y pasa ruff/mypy estricto/pytest. La CI ejecuta las tres puertas de calidad y el smoke test de generación aislada.

**Actividades:**

- Retirar o deprecar formalmente `--mvc` para evitar arquitectura dual.
- Actualizar `doc/arquitectura.md`, diagramas, README de GenCLI y documentación de cada comando.
- Sincronizar REQS-01 y criterios de aceptación con lo implementado.
- Configurar checks de CI: Ruff, MyPy, unit tests, tests de scripts y generación temporal `--hex` + `--uc-*`.
- Ejecutar revisión final: dirección de imports, cero `commit()` en repositorios, cero parsing de errores por string, idempotencia de todos los comandos.

**Entregables:**

- Documentación completa de comandos y arquitectura.
- CI configurada o script único equivalente para validación local/automatizada.
- Checklist final de REQS-01.

**Salida:** Código, templates, scripts, pruebas y documentación describen el mismo sistema; REQS-02 puede comenzar.

## 4. Calendario consolidado

| Fase | Duración | Acumulado | Dependencia |
|---|---:|---:|---|
| 0. Línea base | 0.5 d | 0.5 d | Ninguna |
| 1. Shared kernel | 1.5 d | 2 d | 0 |
| 2. `--hex` | 1.5 d | 3.5 d | 1 |
| 3. Hooks/scripts | 1.5 d | 5 d | 2 |
| 4. `--uc-list` | 1.5 d | 6.5 d | 3 |
| 5. `--uc-list-paginated` | 2 d | 8.5 d | 4 |
| 6. `--uc-find-by` | 2 d | 10.5 d | 5 |
| 7. Create + get | 2 d | 12.5 d | 4 |
| 8. Update + delete | 2 d | 14.5 d | 7 |
| 9. Validación products | 2 d | 16.5 d | 5, 6, 8 |
| 10. Cierre | 1.5 d | **18 d** | Todas |

> La suma de fases es **18 días**. Para ejecución secuencial por una sola persona, planificar 18 días, más 1.5 a 2 días de contingencia.

## 5. Hitos de aprobación

| Hito | Al finalizar | Evidencia requerida |
|---|---|---|
| H1 | Fase 3 | `--hex` y scripts seguros/idempotentes; revisión de marcadores |
| H2 | Fase 6 | Listado, paginación keyset y búsqueda dinámica segura operativos en users |
| H3 | Fase 8 | Todos los comandos `--uc-*` definidos funcionan sobre users |
| H4 | Fase 9 | products valida la generalización del generador |
| H5 | Fase 10 | CI, docs y criterios REQS-01 cerrados |

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Hooks duplican contenido | Pruebas de segunda ejecución desde Fase 3; identificadores únicos por bloque generado |
| Mutación deja Python inválido | Escritura atómica y `ast.parse` previo; no modificar cuando falte un marcador |
| `find-by` expone campos sensibles | Allowlist por entidad; exclusión por defecto de secretos, auditoría, relaciones e IDs internos |
| Paginación lenta a profundidad alta | Cursor/keyset, orden indexado y test que prohíbe `OFFSET` |
| Ruta duplicada entre listados | Convención cerrada D-04 y test de registro de rutas |
| Diferencia manual entre users/products | Fase 9 prohíbe cambios estructurales manuales; toda corrección vuelve al template/script |
| `--mvc` sigue siendo usado | Deprecación visible y eliminación al cierre de Fase 10 |

## 7. Condición para iniciar REQS-02

No se inicia el módulo API Key hasta completar H5. En particular deben estar listos el shared kernel, la inyección por providers, la política UoW, la generación incremental y las garantías de edición idempotente. Así `api_keys` será el primer módulo nuevo construido íntegramente con `--hex` y sus casos de uso específicos.
