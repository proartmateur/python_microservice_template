# Arquitectura hexagonal de 3 capas con generación incremental

Este template genera microservicios con una arquitectura hexagonal (Ports & Adapters)
minimalista de **3 capas por módulo** (`domain`, `use_cases`, `infrastructure`) más un
**shared kernel** transversal. La arquitectura no solo describe el código resultante:
define cómo se crea y evoluciona mediante **GenCLI**, un generador incremental e
idempotente donde cada capacidad del módulo se añade con un comando independiente.

## Capas de un módulo

```
src/modules/<ent>s/
├── domain/                          # CAPA 1: el corazón. Cero dependencias externas.
│   ├── entities.py                  #   Entidad de dominio (dataclass con comportamiento)
│   ├── repositories.py              #   PUERTO de salida: <Ent>Repository (Protocol async)
│   └── exceptions.py                #   <Ent>NotFoundError, <Ent>AlreadyExistsError, ...
│
├── use_cases/                       # CAPA 2: orquestación. Depende SOLO de domain/.
│   ├── create_<ent>s.py             #   1 caso de uso = 1 archivo = 1 responsabilidad
│   ├── list_<ent>s.py               #   Los casos de uso CIERRAN la transacción (uow.commit)
│   └── ...
│
├── infrastructure/                  # CAPA 3: adaptadores (detalles intercambiables)
│   ├── http/                        #   Adaptador DRIVING (entrada)
│   │   ├── routers.py               #     Rutas registradas bajo /api/v1
│   │   ├── schemas.py               #     DTOs Pydantic de petición/respuesta
│   │   ├── controllers/             #     Traducción HTTP → use case
│   │   └── dependencies.py          #     Composition root del módulo (puerto → adaptador)
│   └── persistence/                 #   Adaptador DRIVEN (salida)
│       ├── models.py                #     Modelos SQLAlchemy (Postgres)
│       └── repositories.py          #     Implementa el puerto; solo hace flush()
└── scripts/                         #   Migraciones puntuales del módulo
```

## Shared kernel (transversal)

```
src/shared/
├── domain/                          # Sin dependencias de frameworks
│   ├── errors.py                    # NotFoundError, AlreadyExistsError, ValidationError, ...
│   ├── unit_of_work.py              # PUERTO UnitOfWork (commit/rollback)
│   ├── pagination.py                # KeysetCursor, CursorPage, CursorCodec
│   └── find_by.py                   # FindByCriteria, FindByOperator, FindByResult
└── infrastructure/
    ├── persistence/
    │   ├── database.py              # Motor async, sesión y Base declarativa
    │   └── unit_of_work.py          # UoW sobre AsyncSession
    └── http/
        ├── error_handlers.py        # Dominio → HTTP (RFC 9457 problem+json)
        ├── pagination.py            # HmacCursorCodec (cursor firmado con HMAC-SHA256)
        └── dependencies.py          # Providers comunes (UoW, cursor codec)
```

## Regla de dependencia (la única regla inviolable)

```
┌──────────────────────────────────────────────────────────┐
│  infrastructure/http ──► use_cases ──► domain            │
│          │                                   ▲           │
│          └──► infrastructure/persistence ────┘           │
│               (implementa el puerto de domain)           │
└──────────────────────────────────────────────────────────┘
```

1. `domain/` **no importa** nada de `use_cases/`, `infrastructure/`, fastapi, sqlalchemy
   ni pydantic (protegido por test de arquitectura).
2. `use_cases/` importa solo de `domain/` y `shared/domain/`.
3. `infrastructure/persistence/repositories.py` importa el puerto desde `domain/` y lo
   implementa (`Postgres<Ent>Repository`).
4. `infrastructure/http/**` consume los casos de uso **solo a través de**
   `dependencies.py` (composition root). Ningún controller conoce SQLAlchemy.
5. Los tests de arquitectura además garantizan que ningún adaptador de persistencia
   hace `commit(` y que ningún archivo de `src/` decide errores con string matching
   (`in message`).

## Política transaccional (Unit of Work)

- El **repositorio** solo hace `flush()`: materializa la operación para detectar
  `IntegrityError` en el momento correcto, pero nunca confirma.
- El **caso de uso** de escritura cierra con `await self._unit_of_work.commit()`.
  Un solo commit por petición → operaciones atómicas y componibles.
- Ante error de integridad, el adaptador traduce la excepción de SQLAlchemy a la
  excepción tipada del dominio (`<Ent>AlreadyExistsError`).

## Errores de dominio → HTTP (RFC 9457)

El dominio lanza excepciones tipadas que heredan de `shared/domain/errors.py`.
`shared/infrastructure/http/error_handlers.py` las mapea a respuestas
`application/problem+json` (RFC 9457):

| Excepción de dominio | HTTP |
|---|---|
| `NotFoundError` / `<Ent>NotFoundError` | 404 |
| `AlreadyExistsError` / `<Ent>AlreadyExistsError` | 409 |
| `DomainValidationError` / `InvalidCursorError` | 400 |
| `PermissionDeniedError` | 403 |
| Cualquier otro error | 500 (sin filtrar el stack) |

No existe string matching sobre mensajes de error entre capas.

## Generación incremental con GenCLI

GenCLI genera primero el núcleo estable del módulo (`--hex`) y añade cada capacidad
como un caso de uso vertical e idempotente (`--uc-*`). Ningún comando genera un CRUD
completo por defecto: el módulo crece solo con lo que necesita.

| Comando | Ruta generada | Comportamiento |
|---|---|---|
| `--hex` | (sin rutas) | Núcleo: entidad, puerto, excepciones, modelo, adaptador vacío, dependencies, router y schemas con marcadores. El router **no** se registra en `main.py`. |
| `--uc-list` | `GET /api/v1/<ent>s/` | Listado simple **siempre acotado** (`limit` 1–100, por defecto 50). Orden estable por `(created_at, id)`. |
| `--uc-list-paginated` | `GET /api/v1/<ent>s/paginated` | Paginación **keyset con cursor firmado**, sin `OFFSET` ni `COUNT(*)`. Respuesta `items`, `next_cursor`, `has_next`, `limit`. |
| `--uc-find-by` | `POST /api/v1/<ent>s/find-by` | Búsqueda dinámica controlada por el frontend: `field` + `query` (`operator`, `value`) + `pagination` opcional. |
| `--uc-create` | `POST /api/v1/<ent>s/` | Creación transaccional (201). `flush` en repositorio, `uow.commit()` en el caso de uso; conflicto → 409. |
| `--uc-get` | `GET /api/v1/<ent>s/{identifier}` | Consulta individual de una entidad activa; no encontrado → 404 tipado. |
| `--uc-update` | `PUT /api/v1/<ent>s/{identifier}` | Reemplazo completo del agregado; 404/409 tipados; transacción única. |
| `--uc-delete` | `DELETE /api/v1/<ent>s/{identifier}` | **Soft delete**: fija `deleted_at` en UTC (204). Los eliminados quedan fuera de list/find-by. |

Los comandos `--uc-*` requieren que el módulo base exista: si no existe, fallan sin
modificar archivos y recomiendan ejecutar `--hex` primero. Repetir cualquier comando
no duplica imports, métodos, rutas ni `include_router` (hooks idempotentes).

Las rutas estáticas (`/paginated`, `/find-by`) se registran antes que las dinámicas
(`/{identifier}`) para evitar sombras de enrutado.

### Paginación keyset

`--uc-list-paginated` y `find-by` con `pagination: true` ordenan por `(created_at, id)`
avanzando con una condición keyset: jamás usan `OFFSET`. El cursor es opaco y está
firmado con HMAC-SHA256 usando `PAGINATION_CURSOR_SECRET` (mínimo 32 caracteres);
un cursor alterado o inválido se rechaza con 400. La consulta pide `limit + 1` filas:
la fila extra solo determina `has_next`. El índice parcial requerido por tabla está
documentado en [reqs/04_paginacion_keyset.md](reqs/04_paginacion_keyset.md).

### Find-by y allowlists

`find-by` valida todo antes de tocar persistencia:

- `field` se valida contra una **allowlist** generada desde las propiedades buscables
  de la entidad (por defecto, todas las propiedades declaradas; nunca columnas internas
  como `deleted_at` ni el identificador).
- `operator` se valida contra la allowlist `equals`, `contains`, `starts_with`
  (`contains`/`starts_with` solo para campos `str`).
- `value` se valida por tipo antes de llegar al repositorio.
- El adaptador construye expresiones ORM desde **mapas estáticos** de columnas y
  operadores: nunca interpola `field` u `operator` en SQL.

### Soft delete

El borrado es siempre lógico: `deleted_at` se fija en UTC y todas las lecturas
(`list`, `list_paginated`, `find_by`, `find_by_id`, `update`) filtran
`deleted_at IS NULL`.

## Hooks y marcadores `gencli:*`

GenCLI no edita archivos existentes por sí solo: tras escribir cada template ejecuta
un hook `onDone` (script Python en `.gen_cli/scripts/`) que completa los contratos
de forma idempotente. Los scripts insertan código tras **marcadores explícitos**,
validan el resultado con `ast.parse` antes de persistir (escritura atómica) y no
modifican nada si falta un marcador.

| Marcador | Archivo | Recibe |
|---|---|---|
| `# gencli:router-imports` | `src/main.py`, `routers.py` | Imports de routers/controladores |
| `# gencli:router-includes` | `src/main.py` | `app.include_router(...)` |
| `# gencli:repository-port-imports` / `-methods` | `domain/repositories.py` | Contratos del puerto |
| `# gencli:repository-adapter-imports` / `-methods` | `persistence/repositories.py` | Implementaciones del adaptador |
| `# gencli:use-case-imports` / `# gencli:use-case-providers` | `http/dependencies.py` | Providers del composition root |
| `# gencli:routes` | `routers.py` | Rutas HTTP |
| `# gencli:schema-imports` / `-models` / `-mappers` | `schemas.py` | DTOs y mapeadores |

Guía de comandos: [gencli_comandos.md](gencli_comandos.md).
