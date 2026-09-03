# REQS-01 · Arquitectura Hexagonal de 3 capas

> **Estado:** Propuesto · **Prioridad:** Alta · **Precede a:** REQS-02 (Seguridad)
> **Alcance:** Refactor del template a arquitectura hexagonal minimalista con 3 capas: `domain`, `use_cases`, `persistence` (+ adaptadores HTTP).

---

## 1. Objetivo

Transformar el template actual (2 capas: dominio anémico + infraestructura monolítica) en una arquitectura hexagonal minimalista, extensible y mantenible, donde:

1. El **dominio** no depende de nada externo (ni SQLAlchemy, ni FastAPI, ni Pydantic).
2. Los **casos de uso** orquestan la lógica de aplicación y dependen solo de puertos (interfaces).
3. La **persistencia** y el **HTTP** son detalles de infraestructura (adaptadores) que implementan o consumen puertos.
4. Las dependencias siempre apuntan **hacia adentro**: `http → use_cases → domain ← persistence`.

## 2. Diagnóstico del estado actual

| Problema | Evidencia | Impacto |
|---|---|---|
| Sin capa de casos de uso | Los controllers llaman directo a `ProductRepository(session)` | Lógica de negocio dispersa en la capa HTTP |
| Sin puertos | No existe interfaz abstracta de repositorio | Imposible sustituir adaptadores; acoplamiento a SQLAlchemy |
| Errores por string matching | `if "Ya existe" in message` en controllers | Protocolo de errores frágil entre capas |
| Transacción dentro del repo | `commit()` en cada método del repositorio | Sin Unit of Work; no se pueden componer operaciones atómicas |
| Dominio anémico con fugas | `entities.py` con lógica de ejemplo muerta (`update_email` sobre atributo inexistente) | Sin reglas de negocio reales |
| DI manual | Cada controller instancia su repositorio | Sin composition root; difícil de testear |
| Bugs bloqueantes | `main.py` importa `src.modules.cosas` (inexistente) | La app no arranca |

## 3. Estructura objetivo

### 3.1 Por módulo

```
src/modules/<ent>s/
├── domain/                          # CAPA 1: el corazón. Cero dependencias externas.
│   ├── entities.py                  #   Entidad con comportamiento
│   ├── repositories.py              #   PUERTO de salida: <Ent>Repository (Protocol async)
│   └── exceptions.py                #   <Ent>NotFound, <Ent>AlreadyExists, <Ent>Invalid...
│
├── use_cases/                       # CAPA 2: orquestación. Depende SOLO de domain/.
│   ├── create_<ent>.py              #   1 caso de uso = 1 archivo = 1 responsabilidad
│   ├── get_<ent>.py
│   ├── list_<ents>.py
│   ├── update_<ent>.py
│   └── delete_<ent>.py
│
├── infrastructure/                  # CAPA 3: adaptadores (detalles intercambiables)
│   ├── http/                        #   Adaptador DRIVING (entrada)
│   │   ├── routers.py               #     Declaración de rutas + permissions requeridas
│   │   ├── schemas.py               #     DTOs Pydantic (request/response)
│   │   ├── controllers/             #     Traducción HTTP → use case
│   │   └── dependencies.py          #     Composition root del módulo (binding puerto→adaptador)
│   ├── persistence/                 #   Adaptador DRIVEN (salida)
│   │   ├── models.py                #     Modelos SQLAlchemy
│   │   └── repositories.py          #     Implementa el puerto de domain/
│   └── ...
└── scripts/                         #   Migraciones puntuales (patrón actual, se conserva)
```

### 3.2 Shared kernel (transversal)

```
src/shared/
├── domain/
│   ├── errors.py                    # Excepciones base: NotFoundError, AlreadyExistsError,
│   │                                # ValidationError, PermissionDeniedError
│   └── unit_of_work.py              # PUERTO: UnitOfWork (control transaccional)
└── infrastructure/
    ├── persistence/
    │   └── database.py              # (existente) + adjuste de política de sesión
    └── http/
        ├── error_handlers.py        # Dominio → HTTP (RFC 9457 problem+json)
        └── dependencies.py          # Providers comunes (UoW, settings)
```

### 3.3 Convenciones de naming

- **Entidades**: PascalCase con sufijo `Entity` (`UserEntity`).
- **Puertos**: nombre del rol sin sufijo (`UserRepository`, `UnitOfWork`) — son la abstracción canónica.
- **Adaptadores**: sufijo por tecnología (`PostgresUserRepository` en `persistence/repositories.py`).
- **Casos de uso**: verbo + entidad (`CreateUser`, `GetUser`...). Clase con método `execute()` — facilita inyección de dependencias por constructor.
- Atributos siempre `snake_case` (corrige el typo `isPhisical` → `is_physical`).

## 4. Reglas de dependencia (la única regla inviolable)

```
┌─────────────────────────────────────────────────┐
│  infrastructure/http  ──►  use_cases ──► domain │
│          │                                ▲     │
│          └──► infrastructure/persistence ─┘     │  (implementa el puerto)
└─────────────────────────────────────────────────┘
```

1. `domain/` **no importa** nada de `use_cases/`, `infrastructure/`, fastapi, sqlalchemy o pydantic.
2. `use_cases/` importa solo de `domain/` y `shared/domain/`.
3. `infrastructure/persistence/repositories.py` importa el puerto desde `domain/repositories.py` y lo implementa.
4. `infrastructure/http/**` importa use cases **solo a través de** `dependencies.py` (composition root del módulo).
5. Los use cases **nunca** hacen `commit()`: declaran la intención; la transacción la decide el UoW.

## 5. Contratos de diseño (firmas, no implementación)

### 5.1 Puerto de repositorio (por módulo)

```python
# domain/repositories.py
from typing import Protocol
from src.modules.users.domain.entities import UserEntity

class UserRepository(Protocol):
    async def find_by_id(self, user_id: UUID) -> UserEntity | None: ...
    async def list_paginated(self, limit: int, page: int) -> tuple[list[UserEntity], int, int]: ...
    async def save(self, entity: UserEntity) -> UserEntity: ...     # create/update
    async def soft_delete(self, user_id: UUID) -> bool: ...
```

### 5.2 Caso de uso

```python
# use_cases/create_user.py
class CreateUser:
    def __init__(self, repo: UserRepository, uow: UnitOfWork) -> None: ...

    async def execute(self, nombre: str, email: str) -> UserEntity:
        # reglas de negocio → lanza UserAlreadyExists / ValidationError
        # repo.save() + uow.commit() al final del caso de uso (o vía UoW)
```

### 5.3 Unit of Work

```python
# shared/domain/unit_of_work.py
class UnitOfWork(Protocol):
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
```

Implementación única (`infrastructure`): envuelve la `AsyncSession` actual. **Política transaccional**: el repositorio hace `flush()` (para detectar `IntegrityError` en el momento correcto), el caso de uso cierra con `uow.commit()`. Un solo `commit` por petición → atomicidad componible.

### 5.4 Composition root del módulo

```python
# infrastructure/http/dependencies.py
def get_user_repository(session = Depends(get_db_session)) -> UserRepository:
    return PostgresUserRepository(session)

def get_create_user(repo = Depends(get_user_repository), uow = Depends(get_uow)) -> CreateUser:
    return CreateUser(repo, uow)
```

Los controllers reciben casos de uso ya construidos: `Depends(get_create_user)`. **Ningún controller conoce SQLAlchemy.**

### 5.5 Errores de dominio

- Dominio lanza excepciones tipadas (`UserAlreadyExists(UserExistsError)` heredando de `shared/domain/errors.py`).
- `shared/infrastructure/http/error_handlers.py` registra handlers FastAPI: `NotFoundError→404`, `AlreadyExistsError→409`, `ValidationError→400`, `PermissionDeniedError→403`, fallback→500 sin filtrar stack.
- Se elimina por completo el string matching `"Ya existe" in message`.

## 6. Plan de migración (orden de ejecución)

| Fase | Entregable | Criterio de salida |
|---|---|---|
| **0. Fix bloqueantes** | Quitar import `cosas` de `main.py`; limpiar lógica muerta de entidades; deduplicar dev-deps de `pyproject.toml`; `README.MD` consistente; `__init__.py` faltantes en products | `poe dev` arranca; `poe lint` y `poe typecheck` en verde |
| **1. Shared kernel** | `shared/domain/errors.py`, `shared/domain/unit_of_work.py`, `error_handlers.py` (problem+json), política flush/commit | Handlers registrados y testeados |
| **2. Módulo de referencia: users** | Puerto `UserRepository`, `use_cases/` ×5, `dependencies.py`, repos renombrado a `PostgresUserRepository`, routers/controllers migrados, e2e existente en verde | e2e users pasa sin cambios de contrato HTTP |
| **3. Replicar a products** | Misma estructura; corregir `isPhisical`→`is_physical` | e2e products en verde |
| **4. Plantillas GenCLI** ⚠️ | Nuevas plantillas: `use_case` ×5, `domain/repositories_template.py` (puerto), `domain/exceptions_template.py`, `http/dependencies_template.py`; actualizar controllers/routers templates para consumir use cases; actualizar `arq.json` con nuevos destinos; actualizar `conftest_template.py` y doc de módulo | `gen -m X ...` genera un módulo hexagonal completo y funcional |
| **5. Documentación** | Reescribir `doc/arquitectura.md` (3 capas), actualizar diagramas `.drawio/png` | Docs coherentes con el código |

> ⚠️ **La fase 4 es la crítica**: este repo es una plantilla; si las plantillas GenCLI no se actualizan, cada módulo generado regresa a 2 capas y el refactor muere. La fase 2 debe escribirse pensando "esto será una plantilla".

## 7. Estrategia de testing

| Nivel | Qué | Cómo |
|---|---|---|
| Unit | Casos de uso (reglas de negocio, mapeo de errores) | Repos falsos en memoria que implementan el Protocol; sin DB |
| Unit | Error handlers | `TestClient` con apps mínimas que lanzan cada excepción de dominio |
| Integración | Adaptador Postgres | Opt-in con marker `e2e` (patrón actual `RUN_E2E_*`) |
| E2E | Flujo completo por módulo | Plantilla existente, ajustada a la nueva composición |

La plantilla de tests debe generar: `fake_repository` + `test_<ent>_use_cases.py` (unit) además del e2e actual.

## 8. Criterios de aceptación

- [ ] Ningún archivo de `domain/` importa fastapi/sqlalchemy/pydantic (verificable con `ruff` + regla de imports o test de arquitectura).
- [ ] Ningún controller importa SQLAlchemy ni repositorios concretos.
- [ ] `grep -r "commit()" src/modules/*/infrastructure/persistence/` → 0 resultados.
- [ ] `grep -rn "in message" src/` → 0 resultados.
- [ ] Un use case se puede testear sin levantar Postgres.
- [ ] `gen -m Producto "name:str,price:float"` produce módulo hexagonal completo.
- [ ] e2e existentes pasan sin cambios en contratos HTTP.

## 9. Fuera de alcance (explícito)

- Eventos de dominio / bus de eventos (quedarán como punto de extensión en entidades, sin implementar).
- CQRS, mediatr, o separación read/write.
- Cambiar el ORM o el framework.
- Módulo de seguridad → ver REQS-02.
