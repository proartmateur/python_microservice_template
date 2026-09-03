# RFC: Modo Faker de Persistencia (Desarrollo sin Base de Datos)

- **Estado:** Propuesto
- **Fecha:** 2026-09-03
- **Autor:** Ingeniería
- **Relacionado:** `arq.json`, `src/config.py`, `src/main.py`, `src/shared/`, `.gen_cli/templates/hex/`

## 1. Motivación

Actualmente el microservicio requiere una conexión viva a PostgreSQL para arrancar
(`lifespan` en `src/main.py` fuerza `init_db` + `ping` con reintentos). Esto
dificulta el desarrollo del API cuando:

- La base de datos está fuera de servicio.
- Aún no se ha modelado el esquema de un módulo.
- Se quiere iterar rápidamente sobre los endpoints/casos de uso sin levantar
  infraestructura.

Se desea un **modo faker** que, mediante una variable de entorno, sustituya los
adaptadores de persistencia SQL por adaptadores en memoria que provean datos
realistas (Faker) y permitan ejecutar la API completa sin Postgres.

## 2. Objetivos

1. Permitir arrancar la API **sin PostgreSQL** mediante `REPOSITORY_DATA_SOURCE=faker`.
2. Garantizar **Liskov Substitution Principle**: los adaptadores faker son
   intercambiables con los adaptadores PostgreSQL sin cambiar use cases,
   controllers ni schemas.
3. Que `gen_cli` genere **ambos** adaptadores (Postgres + Faker) para cualquier
   módulo nuevo, de forma que la funcionalidad esté disponible por defecto.
4. Semántica idéntica entre backends para `list`, `list_paginated`, `find_by`
   (keyset cursor, `limit+1`, `has_next`, orden `created_at, id`).
5. Estado coherente entre peticiones en modo faker (store compartido por módulo).
6. Modo faker válido únicamente para desarrollo.

## 3. No objetivos

- Persistencia durable en modo faker (los datos viven en memoria y se pierden al
  detener el servicio).
- Soporte para multiples hilos/instancias de la API en faker (single process).
- Uso de faker en producción.

## 4. Decisiones de diseño

### 4.1 Configuración

`src/config.py` añade:

```python
REPOSITORY_DATA_SOURCE: Literal["database", "faker"] = "database"
```

- Los campos `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_DB` se vuelven
  **opcionales** cuando `REPOSITORY_DATA_SOURCE == "faker"` (validador
  `@model_validator` de Pydantic).
- `PAGINATION_CURSOR_SECRET` se relaja a opcional. En modo faker, si es `None`,
  `get_cursor_codec` genera un **secret efímero** por arranque (suficiente para
  firmar cursores durante la sesión de desarrollo).

### 4.2 Arranque (`lifespan`)

`src/main.py`:

- Si `REPOSITORY_DATA_SOURCE == "faker"`: **omitir** `db_manager.init_db`,
  `ping` y reintentos. Loguear `🧪 Modo faker: sin base de datos`.
- Si `== "database"`: comportamiento actual sin cambios.

### 4.3 Unit of Work

- `UnitOfWork` es `Protocol` (`src/shared/domain/unit_of_work.py`) → se cumple
  LSP por sustitución estructural.
- Nuevo `src/shared/infrastructure/persistence/faker_unit_of_work.py`:
  `FakerUnitOfWork` con `commit`/`rollback` no-op.
- `src/shared/infrastructure/http/dependencies.py`: `get_unit_of_work` bifurca
  según `REPOSITORY_DATA_SOURCE`.
- Reutilizable por **todos** los módulos (no es por agregado).

### 4.4 Repositorio Faker por módulo (gen_cli)

Para cada módulo generado, además del `Postgres<ent>Repository`, se genera un
`Faker<ent>Repository` en
`<path>/infrastructure/persistence/faker_repositories.py`.

Características:

- Implementa el mismo `Protocol` `<ent>Repository` (LSP por sustitución
  estructural, sin herencia).
- **Store singleton por módulo**: `Faker<ent>Store` mantiene
  `self._store: list[<ent>Entity]` y es inyectado vía dependencia. El
  `Faker<ent>Repository` lo recibe en el constructor.
  - Justificación: que `create` seguido de `get` (en otra petición) vea el
    dato, igual que con Postgres. Si el repo fuera por-petición, el estado se
    perdería entre requests.
- Sincronización: `asyncio.Lock` por store para evitar races en mutaciones
  (FastAPI es async). Aceptable para desarrollo single-process.
- **Sembrado con Faker**: en el `__init__` del store se generan entidades
  respetando los props del módulo y garantizando unicidad de campos
  relevantes (p. ej. `email` único). Semilla opcional para tests
  reproducibles.
- Faker **solo dentro del adaptador infra**: nunca en entidades, dominio ni
  use cases.

### 4.5 Métodos del repositorio faker

Comportamiento espejo de `Postgres<ent>Repository`:

| Método              | Comportamiento faker                                                                |
|---------------------|-------------------------------------------------------------------------------------|
| `save`              | Agrega al store. Duplicado de campo único → `<ent>AlreadyExistsError`.              |
| `find_by_id`        | Busca por `id_<snake_name>` con `deleted_at is None`.                               |
| `update`            | Localiza activo, actualiza campos, flush implícito. Duplicado → `AlreadyExistsError`.|
| `soft_delete`       | Marca `deleted_at`. No existe → `<ent>NotFoundError`.                               |
| `list`              | Filtra `deleted_at is None`, ordena por `created_at, id_<snake_name>`, `limit`.     |
| `list_paginated`    | Keyset: si `cursor`, filtra `(created_at, id) > cursor`; ordena; `limit+1`; `has_next`.|
| `find_by`           | Aplica `criteria` (equals/contains/startswith) sobre campo mapeado; opcional keyset.|

- Mismas excepciones de dominio (`<ent>NotFoundError`,
  `<ent>AlreadyExistsError`).
- Mismos tipos de retorno (`<ent>Entity`, `CursorPage[<ent>Entity]`,
  `FindByResult[<ent>Entity]`).

### 4.6 Inyección de dependencias (bifurcación)

`dependencies_template.py` genera un `get_<snake_name>_repository` que bifurca:

```python
def get_<snake_name>_repository(
    session: AsyncSession = Depends(get_db_session),
    store: Faker<ent>Store = Depends(get_faker_<snake_name>_store),
) -> <ent>Repository:
    if get_settings().REPOSITORY_DATA_SOURCE == "faker":
        return Faker<ent>Repository(store)
    return Postgres<ent>Repository(session)
```

- Ambos imports presentes en el template.
- `get_db_session` solo se activa en modo database; en modo faker FastAPI no lo
  resuelve (la rama faker no lo usa). Considerar `Optional`/dependencia
  condicional para evitar que el resolver falle si `db_manager` no está
  inicializado.

## 5. Plan de implementación

### Fase 0 — Configuración ✅
- `src/config.py`: campo `REPOSITORY_DATA_SOURCE`, validador `PG_*` opcional en
  faker, `PAGINATION_CURSOR_SECRET` opcional.
- `.env.example` creado con referencia de variables.
- `doc/instalacion.md` y `README.MD` actualizados.

### Fase 1 — Infraestructura compartida faker ✅
- `src/shared/infrastructure/persistence/faker_unit_of_work.py`:
  `FakerUnitOfWork` (commit/rollback no-op).
- `src/shared/infrastructure/persistence/database.py`: añadida
  `get_optional_db_session` para que los providers bifurcantes no fallen
  cuando la DB no está inicializada.
- `src/shared/infrastructure/http/dependencies.py`: `get_unit_of_work`
  bifurca según `REPOSITORY_DATA_SOURCE`; `get_cursor_codec` genera secret
  efímero en modo faker.
- `src/main.py` `lifespan`: omite `init_db`/`ping`/reintentos en modo faker.
- Verificado: app arranca en faker, `/health` 200.

### Fase 2 — Template `Faker<ent>Repository` (gencli) ✅
- `.gen_cli/templates/hex/repositories_faker_template.py`: genera
  `Faker<ent>Store` (singleton con `asyncio.Lock`, `set[UUID]` de borrados,
  semilla Faker) y `Faker<ent>Repository` con marker
  `# gencli:faker-repository-methods`.
- `src/shared/infrastructure/persistence/faker_helpers.py`: `fake_value` mapea
  tipos Python → Faker (str/int/float/bool/datetime/UUID).
- `faker>=33.0.0` añadido a `pyproject.toml`.

### Fase 3 — Template `dependencies` bifursante ✅
- `.gen_cli/templates/hex/dependencies_template.py`: `get_<snake_name>_repository`
  bifurca `database|faker`; `get_faker_<snake_name>_store` provee singleton.
- Scripts `register_uc_*.py` actualizados para insertar métodos faker
  equivalentes (`save`, `find_by_id`, `update`, `soft_delete`, `list`,
  `list_paginated`, `find_by`) en `# gencli:faker-repository-methods`.
- `arq.json` actualizado: bloque `"hex base"` emite
  `repositories_faker_template.py` →
  `<path>/infrastructure/persistence/faker_repositories.py`.

### Fase 5 — Migrar módulo `users` como referencia ✅
- `src/modules/users/infrastructure/persistence/faker_repositories.py`:
  `FakerUserStore` + `FakerUserRepository` con todos los métodos.
- `src/modules/users/infrastructure/http/dependencies.py`: bifurcación
  `database|faker` + provider del store singleton.
- Smoke test: flujo CRUD completo (list/get/create/update/delete/paginated/
  find-by) pasa en modo faker sin Postgres.

### Fase 6 — Pruebas
- Test e2e con `REPOSITORY_DATA_SOURCE=faker` (sin Postgres) ejecutando CRUD.
  Valida LSP: el mismo test pasa con ambos backends.
- Test unitario del store faker: unicidad, soft_delete, keyset.

## 6. Riesgos y mitigaciones

- **Dependencia `get_db_session` falla si DB no inicializada**: en modo faker,
  la rama que usa `session` no debe ejecutarse. Mitigar con dependencia
  condicional o `Optional[AsyncSession]`.
- **Semántica keyset divergente**: reimplementar con cuidado `limit+1` y
  comparación `(created_at, id)`. Tests e2e compartidos entre backends
  detectan desviaciones.
- **Estado mutable entre tests**: el store es singleton; en tests,
  resetear/aislar por fixture (recrear store o limpiar `_store`).
- **Faker en dominio**: prohibido por diseño; code review + lint.

## 7. Criterios de aceptación

1. `REPOSITORY_DATA_SOURCE=faker` arranca la API sin Postgres.
2. Flujo CRUD completo (create/list/get/update/delete/find_by/list_paginated)
   funciona en faker con misma semántica que database.
3. `gen_cli --hex` genera ambos adaptadores y el `dependencies` bifurcante.
4. Tests e2e pasan con ambos backends.
5. `REPOSITORY_DATA_SOURCE=database` mantiene comportamiento actual sin
   regresiones.

## 8. Referencias

- Puerto: `src/modules/users/domain/repositories.py`
- Adaptador PG: `src/modules/users/infrastructure/persistence/repositories.py`
- Inyección: `src/modules/users/infrastructure/http/dependencies.py`
- UoW: `src/shared/domain/unit_of_work.py`,
  `src/shared/infrastructure/persistence/unit_of_work.py`
- DB manager: `src/shared/infrastructure/persistence/database.py`
- Lifespan: `src/main.py`
- Templates: `.gen_cli/templates/hex/`, `arq.json`