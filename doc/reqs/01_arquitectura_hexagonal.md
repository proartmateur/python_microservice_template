# REQS-01 · Arquitectura Hexagonal de 3 capas

> **Estado:** Propuesto · **Prioridad:** Alta · **Precede a:** REQS-02 (Seguridad)
> **Alcance:** Refactor del template a arquitectura hexagonal minimalista con 3 capas: `domain`, `use_cases`, `persistence` (+ adaptadores HTTP), y rediseño de GenCLI v2 para generación incremental por caso de uso.

---

## 1. Objetivo

Transformar el template actual (2 capas: dominio anémico + infraestructura monolítica) en una arquitectura hexagonal minimalista, extensible y mantenible, donde:

1. El **dominio** no depende de nada externo (ni SQLAlchemy, ni FastAPI, ni Pydantic).
2. Los **casos de uso** orquestan la lógica de aplicación y dependen solo de puertos (interfaces).
3. La **persistencia** y el **HTTP** son detalles de infraestructura (adaptadores) que implementan o consumen puertos.
4. Las dependencias siempre apuntan **hacia adentro**: `http → use_cases → domain ← persistence`.
5. GenCLI genera primero el núcleo estable del módulo y añade cada capacidad como un caso de uso independiente; no genera un CRUD completo por defecto.

## 2. Modelo de generación incremental con GenCLI v2

La arquitectura no solo define el código resultante: define cómo se crea y evoluciona mediante GenCLI. El comando actual `--mvc`, que genera un CRUD completo y acoplado, será reemplazado por comandos pequeños, composables e idempotentes.

### 2.1 Comando base `--hex`

```bash
gen --hex User "nombre:str,email:str"
```

`--hex` crea el **módulo base sin endpoints ni casos de uso**. Su único propósito es establecer el núcleo de dominio y la estructura preparada para crecer:

```
src/modules/users/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entities.py
│   ├── repositories.py       # Puerto inicialmente vacío o con contratos comunes
│   └── exceptions.py
├── use_cases/
│   └── __init__.py
├── infrastructure/
│   ├── __init__.py
│   ├── http/
│   │   ├── __init__.py
│   │   ├── controllers/
│   │   │   └── __init__.py
│   │   └── dependencies.py   # Providers que se amplían con cada --uc-*
│   └── persistence/
│       ├── __init__.py
│       ├── models.py
│       └── repositories.py   # Adaptador inicialmente vacío
└── scripts/
```

No se registra ningún router en `main.py` hasta que el módulo tenga al menos un caso de uso HTTP.

### 2.2 Comandos por caso de uso `--uc-*`

Cada comando incorpora una única capacidad vertical: caso de uso, contrato de repositorio, adaptador de persistencia, DTO/controlador/router HTTP y pruebas asociadas.

| Comando | Genera | Completa mediante scripts idempotentes |
|---|---|---|
| `--uc-list` | `list_<ent>s.py`, controller y ruta `GET /`, schemas de listado, tests unitarios/e2e | Método `list` en puerto y adaptador; provider del caso de uso; import e inclusión de router en `main.py` |
| `--uc-list-paginated` | `list_paginated_<ent>s.py`, controller/ruta `GET /paginated`, schemas de cursor y tests | Método `list_paginated` en puerto y adaptador; provider; router; registro en `main.py` |
| `--uc-create` | Caso de uso de creación, controller/ruta POST, schemas y tests | Método `save`/`create`; provider; router; registro en `main.py` |
| `--uc-get` | Caso de uso de consulta individual, controller/ruta GET `/{id}`, schemas y tests | Método `find_by_id`; provider; router; registro en `main.py` |
| `--uc-find-by` | Caso de uso genérico de búsqueda, controller/ruta `POST /find-by`, payload y schemas de respuesta, pruebas | Método `find_by` en puerto y adaptador; provider; router; registro en `main.py` |
| `--uc-update` | Caso de uso de actualización, controller/ruta PUT/PATCH, schemas y tests | Método de persistencia requerido; provider; router; registro en `main.py` |
| `--uc-delete` | Caso de uso de eliminación lógica, controller/ruta DELETE y tests | Método `soft_delete`; provider; router; registro en `main.py` |

Ejemplo de uso:

```bash
gen --hex User "nombre:str,email:str"
gen --uc-list User "nombre:str,email:str"
gen --uc-create User "nombre:str,email:str"
gen --uc-list-paginated User "nombre:str,email:str"
gen --uc-find-by User "nombre:str,email:str"
```

Los comandos de caso de uso requieren que el módulo base exista. Si no existe, el script debe terminar con un error claro y recomendar ejecutar primero `--hex`.

### 2.3 Semántica de listado y búsqueda

#### `--uc-list`: listado simple acotado

Este caso se reserva para colecciones pequeñas, catálogos controlados o escenarios donde la colección está acotada por una regla de negocio. Nunca puede devolver resultados ilimitados: el use case aplica un `limit` máximo fijo y documentado, incluso si el cliente no lo indica.

#### `--uc-list-paginated`: colecciones grandes

Este caso existe para tablas que pueden alcanzar millones de registros. La implementación de persistencia debe usar paginación por **cursor/keyset**, no `OFFSET`:

- Orden determinista con una clave indexada y estable, típicamente `(created_at, id)` o `(id)`.
- El cliente recibe `items`, `next_cursor`, `has_next` y `limit`.
- La siguiente página usa el cursor recibido; no el número de página.
- `limit` tiene mínimo, máximo y valor por defecto seguros.
- La query selecciona solo las columnas necesarias y usa índices que cubran el orden y filtros aplicados.

El contrato conceptual de respuesta es:

```json
{
  "items": [],
  "next_cursor": "opaque-cursor-or-null",
  "has_next": true,
  "limit": 50
}
```

#### `--uc-find-by`: búsqueda dinámica controlada por el frontend

`--uc-find-by` genera **un único caso de uso genérico**. No se generan comandos por campo ni por operador. En tiempo de ejecución, el frontend decide el campo, criterio y si requiere paginación mediante un payload HTTP:

```json
{
  "field": "name",
  "query": {
    "operator": "equals",
    "value": "pedro"
  },
  "pagination": true,
  "limit": 50,
  "cursor": "opaque-cursor-or-null"
}
```

- Ruta: `POST /<ent>s/find-by`. Es una lectura, pero usa `POST` para transportar un payload de búsqueda estructurado sin exponer criterios complejos en la URL.
- `pagination` es opcional. Si es `true`, usa exactamente el contrato y la estrategia cursor/keyset de `--uc-list-paginated`.
- Si `pagination` es `false` o se omite, devuelve una colección simple **siempre acotada** por un máximo seguro del servidor.
- `field` se valida contra una **allowlist** generada a partir de los campos buscables de la entidad. El frontend no puede consultar columnas no declaradas ni atributos internos.
- `operator` se valida contra una allowlist explícita: inicialmente `equals`, `contains` y `starts_with`. Cada operador se mapea internamente a expresiones SQLAlchemy parametrizadas.
- `value` se valida según el tipo del campo antes de llegar al repositorio.
- El repositorio nunca interpola texto de `field` u `operator` en SQL. Recibe una especificación validada y construye expresiones ORM desde el mapa permitido.

La allowlist debe excluir por defecto identificadores internos, secretos, hashes, campos de auditoría y relaciones. Un módulo puede ampliar la lista de campos buscables de forma explícita en su dominio.

### 2.4 Hooks y scripts de mutación controlada

GenCLI ejecuta `onDone` después de escribir cada template. Los hooks se usarán para ejecutar scripts Python ubicados en `.gen_cli/scripts/`, porque GenCLI por sí solo no inserta contenido en archivos ya creados.

```json
{
  "template": "/hex/use_cases/list_use_case_template.py",
  "destination": "<path>/use_cases/list_<snake_name>s.py",
  "onDone": "python .gen_cli/scripts/register_uc_list.py <path> <snake_name>"
}
```

Los scripts son parte de la arquitectura y deben cumplir estas reglas:

1. **Idempotencia:** ejecutar el mismo comando dos veces no duplica imports, métodos, rutas ni `include_router`.
2. **Un único hook mutador por comando:** para impedir que un mismo script se ejecute una vez por cada archivo generado. Los demás templates del comando no tendrán `onDone` mutador.
3. **Marcadores controlados:** `main.py`, puertos, adaptadores, `dependencies.py` y `routers.py` incluyen marcadores explícitos de GenCLI para inserción ordenada.
4. **Validación sintáctica:** tras mutar Python, el script valida el archivo con `ast.parse`; si falla, revierte el cambio en memoria y termina con error.
5. **Inserciones deterministas:** imports ordenados y bloques agrupados por caso de uso; no se usa reemplazo textual ambiguo.
6. **Fallos seguros:** si el archivo o marcador esperado no existe, no se modifica nada y se informa cómo recuperar el estado.

Marcadores mínimos propuestos:

```python
# main.py
# gencli:router-imports
# gencli:router-includes

# domain/repositories.py
# gencli:repository-port-methods

# infrastructure/persistence/repositories.py
# gencli:repository-adapter-methods

# infrastructure/http/dependencies.py
# gencli:use-case-providers

# infrastructure/http/routers.py
# gencli:routes
```

La implementación de los scripts debe editar la estructura Python de forma segura. En esta primera entrega, los marcadores delimitan el área editable; la validación AST es obligatoria. Una evolución posterior puede sustituir la manipulación por texto por transformaciones AST/CST sin alterar el contrato de los comandos.

## 3. Diagnóstico del estado actual

| Problema | Evidencia | Impacto |
|---|---|---|
| Sin capa de casos de uso | Los controllers llaman directo a `ProductRepository(session)` | Lógica de negocio dispersa en la capa HTTP |
| Sin puertos | No existe interfaz abstracta de repositorio | Imposible sustituir adaptadores; acoplamiento a SQLAlchemy |
| Errores por string matching | `if "Ya existe" in message` en controllers | Protocolo de errores frágil entre capas |
| Transacción dentro del repo | `commit()` en cada método del repositorio | Sin Unit of Work; no se pueden componer operaciones atómicas |
| Dominio anémico con fugas | `entities.py` con lógica de ejemplo muerta (`update_email` sobre atributo inexistente) | Sin reglas de negocio reales |
| DI manual | Cada controller instancia su repositorio | Sin composition root; difícil de testear |
| Bugs bloqueantes | `main.py` importa `src.modules.cosas` (inexistente) | La app no arranca |

## 4. Estructura objetivo

### 4.1 Por módulo

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

### 4.2 Shared kernel (transversal)

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

### 4.3 Convenciones de naming

- **Entidades**: PascalCase con sufijo `Entity` (`UserEntity`).
- **Puertos**: nombre del rol sin sufijo (`UserRepository`, `UnitOfWork`) — son la abstracción canónica.
- **Adaptadores**: sufijo por tecnología (`PostgresUserRepository` en `persistence/repositories.py`).
- **Casos de uso**: verbo + entidad (`CreateUser`, `GetUser`...). Clase con método `execute()` — facilita inyección de dependencias por constructor.
- Atributos siempre `snake_case` (corrige el typo `isPhisical` → `is_physical`).

## 5. Reglas de dependencia (la única regla inviolable)

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

## 6. Contratos de diseño (firmas, no implementación)

### 6.1 Puerto de repositorio (por módulo)

```python
# domain/repositories.py
from typing import Protocol
from src.modules.users.domain.entities import UserEntity

class UserRepository(Protocol):
    async def find_by_id(self, user_id: UUID) -> UserEntity | None: ...
    async def list(self, limit: int) -> list[UserEntity]: ...
    async def list_paginated(
        self, limit: int, cursor: str | None
    ) -> CursorPage[UserEntity]: ...
    async def find_by(self, criteria: FindByCriteria) -> FindByResult: ...
    async def save(self, entity: UserEntity) -> UserEntity: ...     # create/update
    async def soft_delete(self, user_id: UUID) -> bool: ...
```

### 6.2 Caso de uso

```python
# use_cases/create_user.py
class CreateUser:
    def __init__(self, repo: UserRepository, uow: UnitOfWork) -> None: ...

    async def execute(self, nombre: str, email: str) -> UserEntity:
        # reglas de negocio → lanza UserAlreadyExists / ValidationError
        # repo.save() + uow.commit() al final del caso de uso (o vía UoW)
```

### 6.3 Unit of Work

```python
# shared/domain/unit_of_work.py
class UnitOfWork(Protocol):
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
```

Implementación única (`infrastructure`): envuelve la `AsyncSession` actual. **Política transaccional**: el repositorio hace `flush()` (para detectar `IntegrityError` en el momento correcto), el caso de uso cierra con `uow.commit()`. Un solo `commit` por petición → atomicidad componible.

### 6.4 Composition root del módulo

```python
# infrastructure/http/dependencies.py
def get_user_repository(session = Depends(get_db_session)) -> UserRepository:
    return PostgresUserRepository(session)

def get_create_user(repo = Depends(get_user_repository), uow = Depends(get_uow)) -> CreateUser:
    return CreateUser(repo, uow)
```

Los controllers reciben casos de uso ya construidos: `Depends(get_create_user)`. **Ningún controller conoce SQLAlchemy.**

### 6.5 Errores de dominio

- Dominio lanza excepciones tipadas (`UserAlreadyExists(UserExistsError)` heredando de `shared/domain/errors.py`).
- `shared/infrastructure/http/error_handlers.py` registra handlers FastAPI: `NotFoundError→404`, `AlreadyExistsError→409`, `ValidationError→400`, `PermissionDeniedError→403`, fallback→500 sin filtrar stack.
- Se elimina por completo el string matching `"Ya existe" in message`.

## 7. Plan de migración (orden de ejecución)

| Fase | Entregable | Criterio de salida |
|---|---|---|
| **0. Fix bloqueantes** | Quitar import `cosas` de `main.py`; limpiar lógica muerta de entidades; deduplicar dev-deps de `pyproject.toml`; `README.MD` consistente; `__init__.py` faltantes en products | `poe dev` arranca; `poe lint` y `poe typecheck` en verde |
| **1. Shared kernel** | `shared/domain/errors.py`, `shared/domain/unit_of_work.py`, `error_handlers.py` (problem+json), política flush/commit | Handlers registrados y testeados |
| **2. Referencia incremental: users** | Crear users mediante `--hex`; implementar `--uc-list` y `--uc-list-paginated` de extremo a extremo; validar scripts y hooks idempotentes; añadir `--uc-find-by` y los restantes `--uc-*` | Ejecutar `--hex` + cualquier `--uc-*` dos veces no duplica código; e2e users pasa |
| **3. Replicar y validar products** | Generar/refactorizar products exclusivamente con `--hex` + los `--uc-*`; corregir `isPhisical`→`is_physical` según política de compatibilidad | e2e products en verde |
| **4. Productizar GenCLI** ⚠️ | Consolidar templates, `arq.json`, hooks y `.gen_cli/scripts`; generar tests unitarios/fake repository por caso de uso; retirar `--mvc` o deprecarlo explícitamente | `gen --hex X ...` + `gen --uc-list X ...` genera un módulo funcional sin edición manual estructural |
| **5. Documentación** | Reescribir `doc/arquitectura.md` (3 capas + modelo incremental), actualizar diagramas `.drawio/png` y guía de comandos GenCLI | Docs coherentes con el código y el generador |

> ⚠️ **Las fases 2 y 4 son críticas**: el módulo de referencia debe construirse usando los mismos templates, hooks y scripts que usarán los consumidores. Una migración manual de users/products sin comandos `--hex` y `--uc-*` produciría una arquitectura que GenCLI no puede reproducir.

## 8. Estrategia de testing

| Nivel | Qué | Cómo |
|---|---|---|
| Unit | Casos de uso (reglas de negocio, mapeo de errores) | Repos falsos en memoria que implementan el Protocol; sin DB |
| Unit | Error handlers | `TestClient` con apps mínimas que lanzan cada excepción de dominio |
| Unit | Scripts GenCLI | Ejecutar cada script contra fixtures de archivos con/sin marcadores; verificar idempotencia y parseo AST |
| Integración | Generación incremental | `--hex` seguido de cada `--uc-*`; verificar árbol, imports, contrato y no duplicación al repetir |
| Unit/Integración | Paginación por cursor | Primera/siguiente página, cursor inválido, orden estable, límite máximo, consulta sin `OFFSET` |
| Unit/Integración | `find-by` | Campo permitido/no permitido, operador permitido/no permitido, tipos inválidos, con/sin paginación, SQL parametrizado |
| Integración | Adaptador Postgres | Opt-in con marker `e2e` (patrón actual `RUN_E2E_*`) |
| E2E | Flujo completo por módulo | Plantilla existente, ajustada a la nueva composición |

La plantilla de cada `--uc-*` debe generar su prueba de caso de uso y ampliar la prueba e2e del módulo. `--hex` genera el `fake_repository` y las fixtures comunes.

## 9. Criterios de aceptación

- [ ] Ningún archivo de `domain/` importa fastapi/sqlalchemy/pydantic (verificable con `ruff` + regla de imports o test de arquitectura).
- [ ] Ningún controller importa SQLAlchemy ni repositorios concretos.
- [ ] `grep -r "commit()" src/modules/*/infrastructure/persistence/` → 0 resultados.
- [ ] `grep -rn "in message" src/` → 0 resultados.
- [ ] Un use case se puede testear sin levantar Postgres.
- [ ] `gen --hex Producto "name:str,price:float"` genera únicamente el núcleo del módulo, sin router registrado en `main.py`.
- [ ] `gen --uc-list Producto "name:str,price:float"` genera el caso de uso, el endpoint de listado y completa puerto/adaptador/providers mediante scripts.
- [ ] `gen --uc-list-paginated Producto "name:str,price:float"` usa cursor/keyset, devuelve cursor opaco y no genera consultas con `OFFSET`.
- [ ] `gen --uc-find-by Producto "name:str,price:float"` genera un endpoint `POST /productos/find-by` que valida `field`, `operator`, `value` y `pagination`.
- [ ] `find-by` no permite campos ni operadores fuera de la allowlist, ni genera SQL por interpolación de texto recibido.
- [ ] Las respuestas no paginadas de `list` y `find-by` tienen siempre un límite máximo aplicado por el servidor.
- [ ] Repetir el mismo comando `--uc-list` no duplica métodos, imports, rutas ni `app.include_router(...)`.
- [ ] Un comando `--uc-*` contra un módulo inexistente falla sin modificar archivos y explica que debe ejecutarse `--hex` primero.
- [ ] Los archivos mutados por hooks pasan `ast.parse`, Ruff y MyPy.
- [ ] e2e existentes pasan sin cambios en contratos HTTP.

## 10. Fuera de alcance (explícito)

- Eventos de dominio / bus de eventos (quedarán como punto de extensión en entidades, sin implementar).
- CQRS, mediatr, o separación read/write.
- Cambiar el ORM o el framework.
- Módulo de seguridad → ver REQS-02.
- Soporte para eliminar un caso de uso generado o revertir mutaciones de GenCLI automáticamente.
- Transformaciones AST/CST completas; esta entrega usa marcadores controlados, idempotencia y validación AST.
