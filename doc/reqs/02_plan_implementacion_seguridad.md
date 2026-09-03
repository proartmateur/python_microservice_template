# REQS-02 · Plan de implementación — Módulo de Seguridad API Key

> **Documento:** Plan detallado por fases para implementar `02_seguridad_api_key.md`
> **Duración objetivo:** Cada fase ≤ 1 día de trabajo
> **Paralelizable:** Fases 1 y 7 pueden avanzar en paralelo; Fases 5 y 6 son independientes entre sí tras Fase 3.

---

## Resumen de fases

| Fase | Entregable | Depende de | Paralelizable |
|------|-----------|------------|---------------|
| 1 | Migración `api_keys` + dominio (entidad, VOs, puertos, excepciones) + `KeyHasher` HMAC | — | Sí (con F7) |
| 2 | Use cases (create/verify/rotate/revoke) + Postgres adapter + CLI `create_api_key` | F1 | No |
| 3 | HTTP adapter: header extractor, `verify_api_key_dep`, `require_permission`, `AuthContext`; proteger rutas existentes | F2 | No |
| 4 | `RoleAccessPolicy` + tests de la matriz de permisos | F3 | No |
| 5 | Estrategia `redis_cache` (decorador) + invalidación activa + fallback | F2 | Sí (con F6) |
| 6 | Rate limiter propio (sliding window) + headers 429 + fallback memoria | F3 | Sí (con F5) |
| 7 | Hardening: security headers, CORS, docs gating, request-id, audit log | — | Sí (con F1) |
| 8 | Plantillas GenCLI: routers nuevos nacen con `require_permission`; doc actualizada | F3, F4 | No |
| 9 | GenCLI `--uc-delete-<uc>`: elimina solo los archivos de un UC + script `protect_module.py`/`unprotect_module.py` | F8 | No |

---

## Fase 1 — Migración `api_keys` + dominio + `KeyHasher` HMAC

**Objetivo:** Crear el núcleo de dominio del módulo `api_keys` con entidad, value objects, puertos, excepciones y el servicio criptográfico `KeyHasher`.

### Archivos a crear

```
src/modules/api_keys/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entities.py              # ApiKeyEntity
│   ├── value_objects.py         # RawApiKey, KeyHash, KeyPrefix, KeyStatus
│   ├── repositories.py          # ApiKeyRepository (Protocol)
│   ├── services.py              # KeyHasher (Protocol)
│   └── exceptions.py            # InvalidApiKeyError, ExpiredApiKeyError, ...
├── infrastructure/
│   ├── __init__.py
│   └── persistence/
│       ├── __init__.py
│       └── models.py            # ApiKeyModel (SQLAlchemy)
└── scripts/
    ├── __init__.py
    ├── create_api_keys_table.py
    └── create_api_keys_index.py

src/shared/domain/auth_context.py  # AuthContext
src/shared/infrastructure/security/
├── __init__.py
└── hmac_key_hasher.py             # HmacKeyHasher (implementación del puerto)
```

### Detalle por archivo

#### `src/modules/api_keys/domain/entities.py`

```python
@dataclass
class ApiKeyEntity:
    name: str
    key_prefix: str        # p.ej. "pk_a1b2c3d4"
    key_hash: str          # HMAC-SHA256 hex (64 chars)
    role: str              # "admin" | "write" | "read"
    status: str            # "active" | "revoked"
    id_api_key: UUID = field(default_factory=uuid7)
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None
    created_at: datetime = field(default_factory=get_utc_now)
```

#### `src/modules/api_keys/domain/value_objects.py`

- `RawApiKey`: wrapper de la clave en claro (solo en RAM, nunca se persiste).
  - Factory `RawApiKey.generate()` → usa `secrets.token_urlsafe(32)`, formato `pk_<8hex>_<secret43>`.
  - Propiedad `prefix` → primeros 12 chars.
  - Propiedad `secret` → parte después del prefijo.
  - Validación de formato en constructor.
- `KeyHash`: wrapper del hash hex (64 chars).
- `KeyPrefix`: wrapper del prefijo (valida formato `pk_` + 8 hex).
- `KeyStatus`: enum `StrEnum` con `ACTIVE = "active"` y `REVOKED = "revoked"`.

#### `src/modules/api_keys/domain/repositories.py`

```python
class ApiKeyRepository(Protocol):
    async def find_by_prefix(self, prefix: str) -> ApiKeyEntity | None: ...
    async def save(self, entity: ApiKeyEntity) -> ApiKeyEntity: ...
    async def revoke(self, identifier: UUID) -> None: ...
    async def update_hash(self, identifier: UUID, new_hash: str) -> None: ...
    async def update_last_used(self, identifier: UUID, at: datetime) -> None: ...
    async def list(self, *, limit: int) -> list[ApiKeyEntity]: ...
    async def find_by_id(self, identifier: UUID) -> ApiKeyEntity | None: ...
```

#### `src/modules/api_keys/domain/services.py`

```python
class KeyHasher(Protocol):
    def hash(self, raw_secret: str) -> str: ...
    def verify(self, raw_secret: str, key_hash: str) -> bool: ...
```

#### `src/modules/api_keys/domain/exceptions.py`

Heredar de `src/shared/domain/errors.py`:

```python
class InvalidApiKeyError(DomainError): ...
class ExpiredApiKeyError(DomainError): ...
class RevokedApiKeyError(DomainError): ...
class InsufficientRoleError(PermissionDeniedError): ...
```

#### `src/shared/domain/auth_context.py`

```python
@dataclass(frozen=True)
class AuthContext:
    key_id: UUID
    name: str
    role: str
    key_prefix: str
```

#### `src/shared/infrastructure/security/hmac_key_hasher.py`

```python
class HmacKeyHasher:
    def __init__(self, pepper: str) -> None: ...
    def hash(self, raw_secret: str) -> str:
        # HMAC-SHA256(raw_secret, pepper) → hex digest (64 chars)
    def verify(self, raw_secret: str, key_hash: str) -> bool:
        # hmac.compare_digest(self.hash(raw_secret), key_hash)
```

#### `src/modules/api_keys/infrastructure/persistence/models.py`

Tabla `api_keys` según esquema §3.1 del req.

#### Scripts de migración

- `create_api_keys_table.py`: crea tabla + índice parcial `ix_api_keys_prefix` (sigue el patrón de `create_users_table.py`).
- `create_api_keys_index.py`: crea solo el índice.
- Añadir tareas `create_api_keys_table` y `create_api_keys_index` a `pyproject.toml`.

#### `src/config.py`

Añadir settings:
```python
SECURITY_PEPPER: str = Field(default="", min_length=32)
```
Validador: si `REPOSITORY_DATA_SOURCE == "database"` y `SECURITY_PEPPER` es vacío o < 32 chars → error.

### Casos de uso

- **CU-1.1**: Generar una `RawApiKey` → tiene formato `pk_<8hex>_<secret43>`, prefijo extraíble.
- **CU-1.2**: Hashear un secret con `HmacKeyHasher` → mismo input produce mismo hash (determinista con pepper).
- **CU-1.3**: Verificar un secret contra un hash → `True` si coinciden, `False` si no (constant-time).

### Criterios de aceptación

- [ ] `ApiKeyEntity` contiene todos los campos del esquema §3.1.
- [ ] `RawApiKey.generate()` produce claves con formato `pk_<8hex>_<43+chars>`.
- [ ] `RawApiKey` valida formato en constructor ( ValueError si malformada).
- [ ] `HmacKeyHasher.hash()` devuelve 64 chars hex.
- [ ] `HmacKeyHasher.verify()` usa `hmac.compare_digest` (constant-time).
- [ ] `ApiKeyRepository` es `Protocol` con los 7 métodos del puerto.
- [ ] `AuthContext` es `frozen dataclass` con `key_id`, `name`, `role`, `key_prefix`.
- [ ] Excepciones heredan de `DomainError` / `PermissionDeniedError`.
- [ ] `ApiKeyModel` define tabla `api_keys` con índice único parcial en `key_prefix WHERE status = 'active'`.
- [ ] Scripts de migración validan `REPOSITORY_DATA_SOURCE=database`.
- [ ] `mypy --strict` y `ruff` limpios.

### Happy path

```python
raw = RawApiKey.generate()
assert raw.prefix.startswith("pk_")
assert len(raw.secret) >= 43

hasher = HmacKeyHasher(pepper="a" * 32)
h = hasher.hash(raw.secret)
assert len(h) == 64
assert hasher.verify(raw.secret, h) is True
```

### Sad path

```python
# Formato malformado
with pytest.raises(ValueError):
    RawApiKey("not-a-valid-key")

# Pepper demasiado corto
with pytest.raises(ValueError):
    HmacKeyHasher(pepper="short")

# Verify con hash distinto
assert hasher.verify(raw.secret, "0" * 64) is False
```

---

## Fase 2 — Use cases + Postgres adapter + CLI `create_api_key`

**Objetivo:** Implementar los 4 use cases del módulo, el adaptador PostgreSQL del puerto `ApiKeyRepository`, y un CLI de emisión.

### Archivos a crear

```
src/modules/api_keys/use_cases/
├── __init__.py
├── verify_api_key.py           # raw key → ApiKeyEntity validada o excepción
├── create_api_key.py           # genera raw key, devuelve (entity, raw)
├── rotate_api_key.py           # nuevo secret, mismo id/name/role
└── revoke_api_key.py           # marca revoked_at + status

src/modules/api_keys/infrastructure/persistence/
├── repositories.py             # PostgresApiKeyRepository
└── faker_repositories.py       # FakerApiKeyRepository (modo faker)

src/modules/api_keys/scripts/
└── create_api_key.py           # CLI: imprime raw key una sola vez

src/modules/api_keys/infrastructure/http/
├── __init__.py
└── dependencies.py             # composition root del módulo
```

### Detalle por use case

#### `verify_api_key.py`

```python
class VerifyApiKey:
    def __init__(self, repository: ApiKeyRepository, hasher: KeyHasher) -> None: ...

    async def execute(self, raw_key: str) -> AuthContext:
        # 1. Parsear prefijo + secret de raw_key
        # 2. repository.find_by_prefix(prefix) → entity | None
        # 3. Si None → InvalidApiKeyError
        # 4. hasher.verify(secret, entity.key_hash) → bool
        # 5. Si False → InvalidApiKeyError
        # 6. Si status == "revoked" → RevokedApiKeyError
        # 7. Si expires_at and expires_at < now → ExpiredApiKeyError
        # 8. return AuthContext(key_id, name, role, key_prefix)
```

#### `create_api_key.py`

```python
class CreateApiKey:
    def __init__(self, repository: ApiKeyRepository, hasher: KeyHasher, uow: UnitOfWork) -> None: ...

    async def execute(self, *, name: str, role: str, expires_at: datetime | None = None) -> tuple[ApiKeyEntity, RawApiKey]:
        # 1. raw = RawApiKey.generate()
        # 2. key_hash = hasher.hash(raw.secret)
        # 3. entity = ApiKeyEntity(name, raw.prefix, key_hash, role, ...)
        # 4. repository.save(entity)
        # 5. uow.commit()
        # 6. return (entity, raw)  ← raw se muestra UNA vez
```

#### `rotate_api_key.py`

```python
class RotateApiKey:
    def __init__(self, repository: ApiKeyRepository, hasher: KeyHasher, uow: UnitOfWork) -> None: ...

    async def execute(self, identifier: UUID) -> RawApiKey:
        # 1. raw = RawApiKey.generate()
        # 2. new_hash = hasher.hash(raw.secret)
        # 3. repository.update_hash(identifier, new_hash)
        # 4. uow.commit()
        # 5. return raw
```

#### `revoke_api_key.py`

```python
class RevokeApiKey:
    def __init__(self, repository: ApiKeyRepository, uow: UnitOfWork) -> None: ...

    async def execute(self, identifier: UUID) -> None:
        # 1. repository.revoke(identifier)
        # 2. uow.commit()
```

#### `PostgresApiKeyRepository`

Implementa los 7 métodos del puerto usando `AsyncSession` + `select(ApiKeyModel)`:
- `find_by_prefix`: filtra por `key_prefix` + `status == 'active'`.
- `save`: `session.add(model)` + `flush`.
- `revoke`: busca por id, set `status='revoked'` + `revoked_at=now()`.
- `update_hash`: busca por id, set `key_hash` + `key_prefix` (nuevo prefijo).
- `update_last_used`: busca por id, set `last_used_at`.
- `list`: filtra activas, ordena por `created_at`, `limit`.
- `find_by_id`: busca por id.

#### `FakerApiKeyRepository`

Store en memoria con 3 claves sembradas (admin/write/read) para desarrollo sin DB.

#### CLI `create_api_key.py`

```python
"""Emite una API key e imprime la raw key una sola vez.

Uso:
    uv run poe create_api_key --name "MiCliente" --role write
"""
```
- Parsea args via `argparse`.
- Llama `CreateApiKey.execute()`.
- Imprime: `API Key creada: pk_a1b2c3d4_Xy...` (una sola vez).
- Imprime: `Guarda esta clave ahora. No se volverá a mostrar.`

#### `dependencies.py`

Composition root del módulo:
- `get_key_hasher()` → `HmacKeyHasher(get_settings().SECURITY_PEPPER)`.
- `get_api_key_repository(session)` → bifurcación `database|faker` como en users.
- Providers para cada use case.

### Casos de uso

- **CU-2.1**: Crear API key → devuelve entity + raw key; raw key tiene formato válido; hash se persiste.
- **CU-2.2**: Verificar API key válida → devuelve `AuthContext` con datos correctos.
- **CU-2.3**: Verificar API key inexistente → `InvalidApiKeyError`.
- **CU-2.4**: Verificar API key revocada → `RevokedApiKeyError`.
- **CU-2.5**: Verificar API key expirada → `ExpiredApiKeyError`.
- **CU-2.6**: Rotar API key → nuevo hash, mismo id/name/role; raw key anterior ya no verifica.
- **CU-2.7**: Revocar API key → `status='revoked'`, `revoked_at` set.
- **CU-2.8**: CLI crea key → imprime raw key una sola vez.

### Criterios de aceptación

- [ ] Los 4 use cases dependen solo de `Protocol`s (Repository, Hasher, UoW).
- [ ] `VerifyApiKey` sigue el flujo §3.3 exacto: prefix → lookup → verify → status → expiry.
- [ ] `CreateApiKey` devuelve `(entity, raw)`; raw nunca se persiste.
- [ ] `RotateApiKey` genera nuevo secret + hash; el anterior falla al verificar.
- [ ] `RevokeApiKey` marca `status='revoked'` + `revoked_at`.
- [ ] `PostgresApiKeyRepository` implementa los 7 métodos del puerto.
- [ ] `FakerApiKeyRepository` funciona en modo faker sin DB.
- [ ] CLI imprime la raw key una sola vez con warning.
- [ ] `mypy --strict` y `ruff` limpios.
- [ ] Tests unitarios de cada use case pasan.

### Happy path

```python
# Crear
entity, raw = await create_uc.execute(name="Cliente1", role="write")
assert raw.prefix == entity.key_prefix

# Verificar
ctx = await verify_uc.execute(str(raw))
assert ctx.role == "write"
assert ctx.name == "Cliente1"

# Rotar
new_raw = await rotate_uc.execute(entity.id_api_key)
assert str(new_raw) != str(raw)

# Verificar con nueva key
ctx2 = await verify_uc.execute(str(new_raw))
assert ctx2.key_id == entity.id_api_key

# Verificar con key antigua → falla
with pytest.raises(InvalidApiKeyError):
    await verify_uc.execute(str(raw))
```

### Sad path

```python
# Key inexistente
with pytest.raises(InvalidApiKeyError):
    await verify_uc.execute("pk_zzzzzzzz_invalid_secret_43_chars_here_xxxxxx")

# Key revocada
await revoke_uc.execute(entity.id_api_key)
with pytest.raises(RevokedApiKeyError):
    await verify_uc.execute(str(new_raw))

# Key expirada
entity_exp, raw_exp = await create_uc.execute(
    name="Expirada", role="read",
    expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
)
with pytest.raises(ExpiredApiKeyError):
    await verify_uc.execute(str(raw_exp))

# Pepper distinto → verify falla
hasher2 = HmacKeyHasher(pepper="b" * 32)
verify_uc2 = VerifyApiKey(repo, hasher2)
with pytest.raises(InvalidApiKeyError):
    await verify_uc2.execute(str(raw))
```

---

## Fase 3 — HTTP adapter: header extractor, auth deps, proteger rutas

**Objetivo:** Crear el adaptador HTTP de autenticación que extrae la API key del header, la verifica, y protege rutas existentes.

### Archivos a crear

```
src/modules/api_keys/infrastructure/http/
├── api_key_header.py          # extract_api_key(request) → str | None
├── auth_dependencies.py       # verify_api_key_dep, require_permission(...)
├── routers.py                 # CRUD de api_keys (protegido con rol admin)
├── schemas.py
├── controllers/
│   ├── __init__.py
│   ├── create_api_key_controller.py
│   ├── list_api_keys_controller.py
│   ├── get_api_key_controller.py
│   ├── rotate_api_key_controller.py
│   └── revoke_api_key_controller.py
└── dependencies.py            # (ampliar el de Fase 2)

src/shared/infrastructure/http/
└── auth_errors.py             # AuthError handlers (401, 403) con WWW-Authenticate
```

### Archivos a modificar

- `src/main.py`: registrar router de `api_keys`, registrar auth error handlers.
- `src/modules/users/infrastructure/http/routers.py`: añadir `dependencies=[Depends(require_permission("users:read"))]` al router.
- `src/shared/infrastructure/http/error_handlers.py`: añadir handler para 401 con `WWW-Authenticate: Bearer`.

### Detalle

#### `api_key_header.py`

```python
def extract_api_key(request: Request) -> str | None:
    """Único punto de extracción del header. Soporta Bearer por defecto."""
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:]
    return None
```

#### `auth_dependencies.py`

```python
async def verify_api_key_dep(
    request: Request,
    verify_uc: VerifyApiKey = Depends(get_verify_api_key),
) -> AuthContext:
    raw = extract_api_key(request)
    if raw is None:
        raise AuthMissingError("Missing API key")
    return await verify_uc.execute(raw)

```

Para `require_permission`, en esta fase se implementa una versión mínima que valida el rol directamente (Fase 4 introduce `AccessPolicy`):

```python
def require_permission(permission: str) -> Callable:
    async def dep(ctx: AuthContext = Depends(verify_api_key_dep)) -> AuthContext:
        # Fase 3: validación directa por rol
        # Fase 4: delegar a AccessPolicy.can(ctx, permission)
        return ctx
    return dep
```

#### `auth_errors.py`

- `AuthMissingError` → 401 + `WWW-Authenticate: Bearer`.
- `InvalidApiKeyError`, `ExpiredApiKeyError`, `RevokedApiKeyError` → 401.
- `InsufficientRoleError` → 403.
- Todos en formato `problem+json`.

#### Schemas de `api_keys`

- `ApiKeyCreateRequest`: `name`, `role`, `expires_at?`.
- `ApiKeyCreateResponse`: `id`, `name`, `key_prefix`, `role`, `status`, `expires_at`, `created_at`. **Nunca** `key_hash`.
- `ApiKeyCreateWithTokenResponse`: extiende `ApiKeyCreateResponse` + `api_key: str` (raw, solo en creación).
- `ApiKeyResponse`: sin `api_key` ni `key_hash`.
- `ApiKeyRotateResponse`: `api_key: str` (raw, solo en rotación).

#### Routers de `api_keys`

Todos protegidos con `require_permission("api_keys:admin")`:
- `POST /api/v1/api-keys/` → crear.
- `GET /api/v1/api-keys/` → listar.
- `GET /api/v1/api-keys/{id}` → consultar.
- `POST /api/v1/api-keys/{id}/rotate` → rotar.
- `DELETE /api/v1/api-keys/{id}` → revocar.

### Casos de uso

- **CU-3.1**: Request sin header → 401 + `WWW-Authenticate: Bearer`.
- **CU-3.2**: Request con key inválida → 401.
- **CU-3.3**: Request con key válida → pasa al endpoint.
- **CU-3.4**: CRUD de api_keys protegido con rol admin.
- **CU-3.5**: Rutas de `users` protegidas con `require_permission("users:read")`.

### Criterios de aceptación

- [ ] `extract_api_key` es la única función que toca el header (§5).
- [ ] Sin header → 401 con `WWW-Authenticate: Bearer`.
- [ ] Key inválida/expirada/revocada → 401.
- [ ] Key válida → `AuthContext` disponible en el endpoint.
- [ ] Rutas de `users` requieren permiso `users:read`.
- [ ] CRUD de `api_keys` requiere permiso `api_keys:admin`.
- [ ] Respuestas de `api_keys` nunca incluyen `key_hash`.
- [ ] Raw key solo aparece en `ApiKeyCreateWithTokenResponse` y `ApiKeyRotateResponse`.
- [ ] Todos los errores 401/403 en `problem+json`.
- [ ] `mypy --strict` y `ruff` limpios.

### Happy path

```bash
# Crear key admin via CLI
uv run poe create_api_key --name "Admin" --role admin
# → API Key creada: pk_a1b2c3d4_Xy...

# Listar users con key válida
curl -H "Authorization: Bearer pk_a1b2c3d4_Xy..." \
     http://localhost:8000/api/v1/users/?limit=5
# → 200, lista de users

# Crear otra key via API (requiere admin)
curl -X POST -H "Authorization: Bearer pk_a1b2c3d4_Xy..." \
     -H "Content-Type: application/json" \
     -d '{"name":"Cliente1","role":"write"}' \
     http://localhost:8000/api/v1/api-keys/
# → 201, {"id":"...","api_key":"pk_...","key_prefix":"pk_...","role":"write",...}
```

### Sad path

```bash
# Sin header
curl http://localhost:8000/api/v1/users/
# → 401, {"title":"No autenticado",...}, WWW-Authenticate: Bearer

# Key inválida
curl -H "Authorization: Bearer pk_zzzzzzzz_invalid" \
     http://localhost:8000/api/v1/users/
# → 401, {"title":"No autenticado",...}

# Key write intentando crear api_key
curl -X POST -H "Authorization: Bearer pk_write_key..." \
     http://localhost:8000/api/v1/api-keys/
# → 403, {"title":"Acceso denegado",...}

# Key revocada
curl -H "Authorization: Bearer pk_revoked..." \
     http://localhost:8000/api/v1/users/
# → 401
```

---

## Fase 4 — `RoleAccessPolicy` + tests de la matriz de permisos

**Objetivo:** Implementar el puerto `AccessPolicy` con `RoleAccessPolicy` y la matriz de permisos por rol.

### Archivos a crear

```
src/shared/domain/access_policy.py          # AccessPolicy (Protocol), Permission (NewType)
src/modules/api_keys/domain/role_policy.py  # ROLE_PERMISSIONS + RoleAccessPolicy
src/modules/api_keys/infrastructure/http/
└── access_policy_dep.py                    # get_access_policy() → RoleAccessPolicy
```

### Archivos a modificar

- `src/modules/api_keys/infrastructure/http/auth_dependencies.py`: `require_permission` ahora delega a `AccessPolicy.can()`.

### Detalle

#### `src/shared/domain/access_policy.py`

```python
Permission = NewType("Permission", str)

class AccessPolicy(Protocol):
    def can(self, ctx: AuthContext, required: Permission) -> bool: ...
```

#### `src/modules/api_keys/domain/role_policy.py`

```python
ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "admin": frozenset({"*"}),
    "write": frozenset({"*:read", "*:write"}),
    "read":  frozenset({"*:read"}),
}

class RoleAccessPolicy:
    def can(self, ctx: AuthContext, required: Permission) -> bool:
        perms = ROLE_PERMISSIONS.get(ctx.role, frozenset())
        if "*" in perms:
            return True
        # Resolver wildcards: "*:read" cubre "users:read", "api_keys:read", etc.
        parts = required.split(":")
        if len(parts) == 2:
            wildcard = f"*:{parts[1]}"
            if wildcard in perms:
                return True
        return required in perms
```

#### `auth_dependencies.py` (modificado)

```python
def require_permission(permission: str) -> Callable:
    async def dep(
        ctx: AuthContext = Depends(verify_api_key_dep),
        policy: AccessPolicy = Depends(get_access_policy),
    ) -> AuthContext:
        if not policy.can(ctx, Permission(permission)):
            raise InsufficientRoleError(f"Requires permission: {permission}")
        return ctx
    return dep
```

### Casos de uso

- **CU-4.1**: Rol `admin` → puede todo (wildcard `*`).
- **CU-4.2**: Rol `write` → puede `*:read` y `*:write` (cubre `users:read`, `users:write`, etc.).
- **CU-4.3**: Rol `read` → solo `*:read`.
- **CU-4.4**: Rol desconocido → denegar todo.
- **CU-4.5**: Permiso `api_keys:admin` solo lo tiene `admin`.

### Criterios de aceptación

- [ ] `AccessPolicy` es `Protocol` con método `can(ctx, required) -> bool`.
- [ ] `RoleAccessPolicy` resuelve wildcards `*` y `*:read`/`*:write`.
- [ ] `require_permission` delega a `AccessPolicy.can()`.
- [ ] Matriz de permisos completa (tabla de la §6.2) cubierta por tests.
- [ ] Rol desconocido → `can()` devuelve `False`.
- [ ] `mypy --strict` y `ruff` limpios.

### Happy path

```python
policy = RoleAccessPolicy()
admin_ctx = AuthContext(key_id=uuid7(), name="admin", role="admin", key_prefix="pk_x")
assert policy.can(admin_ctx, Permission("users:read")) is True
assert policy.can(admin_ctx, Permission("api_keys:admin")) is True

write_ctx = AuthContext(key_id=uuid7(), name="write", role="write", key_prefix="pk_y")
assert policy.can(write_ctx, Permission("users:write")) is True
assert policy.can(write_ctx, Permission("users:read")) is True
```

### Sad path

```python
write_ctx = AuthContext(key_id=uuid7(), name="write", role="write", key_prefix="pk_y")
assert policy.can(write_ctx, Permission("api_keys:admin")) is False

read_ctx = AuthContext(key_id=uuid7(), name="read", role="read", key_prefix="pk_z")
assert policy.can(read_ctx, Permission("users:write")) is False

unknown_ctx = AuthContext(key_id=uuid7(), name="x", role="superuser", key_prefix="pk_w")
assert policy.can(unknown_ctx, Permission("users:read")) is False
```

---

## Fase 5 — Estrategia `redis_cache` (decorador) + invalidación + fallback

**Objetivo:** Implementar `CachedApiKeyRepository` como decorador sobre `PostgresApiKeyRepository` con caché Redis, invalidación activa y fallback a Postgres.

### Dependencias

- Cliente Redis async (usar `redis[hiredis]` ya que `REDIS_URL` ya está en config).

### Archivos a crear

```
src/shared/infrastructure/persistence/redis_client.py   # RedisClient singleton
src/modules/api_keys/infrastructure/persistence/
└── cached_repository.py    # CachedApiKeyRepository (decorador)
```

### Archivos a modificar

- `src/config.py`: añadir `SECURITY_KEY_LOOKUP: Literal["postgres","redis_cache"] = "postgres"`, `SECURITY_KEY_CACHE_TTL: int = 60`, `SECURITY_KEY_CACHE_NEG_TTL: int = 10`.
- `src/modules/api_keys/infrastructure/http/dependencies.py`: bifurcar según `SECURITY_KEY_LOOKUP`.
- `pyproject.toml`: añadir `redis[hiredis]>=5.0.0`.

### Detalle

#### `redis_client.py`

```python
class RedisManager:
    def __init__(self) -> None: ...
    def init(self, url: str) -> None: ...
    async def get(self, key: str) -> str | None: ...
    async def setex(self, key: str, ttl: int, value: str) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def ping(self) -> None: ...
    async def close(self) -> None: ...

redis_manager = RedisManager()
```

#### `cached_repository.py`

```python
class CachedApiKeyRepository:
    """Decorador que cachea lookups por key_prefix."""

    def __init__(self, inner: ApiKeyRepository, redis: RedisManager, ttl: int, neg_ttl: int) -> None: ...

    async def find_by_prefix(self, prefix: str) -> ApiKeyEntity | None:
        # 1. redis.get(f"apikey:{prefix}") → hit?
        # 2. Si "null" → None (caché negativo anti-enumeración)
        # 3. Si serializado → desserializar y devolver
        # 4. Miss → inner.find_by_prefix(prefix)
        # 5. Cachear positivo (ttl) o negativo (neg_ttl)
        # 6. Si Redis cae → log warning + devolver inner (fail-open a DB)

    async def revoke(self, identifier: UUID) -> None:
        # 1. inner.revoke(identifier)
        # 2. Buscar prefix para invalidar caché
        # 3. redis.delete(f"apikey:{prefix}")

    async def update_hash(self, identifier: UUID, new_hash: str) -> None:
        # 1. inner.update_hash(identifier, new_hash)
        # 2. Invalidar caché del prefix anterior y nuevo
```

### Casos de uso

- **CU-5.1**: Primer lookup → miss → query Postgres → cachear.
- **CU-5.2**: Segundo lookup → hit Redis → sin query Postgres.
- **CU-5.3**: Lookup de prefijo inexistente → caché negativo (anti-enumeración).
- **CU-5.4**: Revocar → invalida caché → siguiente lookup va a Postgres.
- **CU-5.5**: Rotar → invalida caché anterior + nuevo.
- **CU-5.6**: Redis cae → fallback a Postgres + log warning.

### Criterios de aceptación

- [ ] `CachedApiKeyRepository` implementa el mismo `Protocol` que `PostgresApiKeyRepository`.
- [ ] `verify_api_key` no sabe cuál repositorio está activo (LSP).
- [ ] Cambiar `SECURITY_KEY_LOOKUP` no requiere cambios de código.
- [ ] Revocación invalida caché activamente (no espera TTL).
- [ ] Caché negativo previene enumeración de prefijos.
- [ ] Redis cae → degrada a Postgres (nunca fail-open a permitir acceso).
- [ ] `mypy --strict` y `ruff` limpios.

### Happy path

```python
# Primer lookup → miss → DB
entity = await cached_repo.find_by_prefix("pk_a1b2c3d4")
# Segundo lookup → hit Redis
entity2 = await cached_repo.find_by_prefix("pk_a1b2c3d4")
assert entity == entity2

# Revocar → invalida
await cached_repo.revoke(entity.id_api_key)
# Siguiente lookup → miss → DB → None (o revocada)
entity3 = await cached_repo.find_by_prefix("pk_a1b2c3d4")
```

### Sad path

```python
# Prefijo inexistente → caché negativo
result = await cached_repo.find_by_prefix("pk_zzzzzzzz")
assert result is None
# Segundo lookup → hit caché negativo (sin DB)

# Redis cae → fallback
redis_manager._client = None  # simular caída
entity = await cached_repo.find_by_prefix("pk_a1b2c3d4")
# → log warning + query Postgres directo
```

---

## Fase 6 — Rate limiter propio (sliding window) + headers 429 + fallback memoria

**Objetivo:** Implementar rate limiting por API key con sliding window sobre Redis, fallback en memoria, y headers estándar.

### Archivos a crear

```
src/shared/infrastructure/rate_limit/
├── __init__.py
├── rate_limiter.py           # RateLimiter (Protocol), RateLimitResult
├── redis_rate_limiter.py     # RedisRateLimiter (Lua + ZSET)
├── memory_rate_limiter.py    # MemoryRateLimiter (fallback)
└── rate_limit_middleware.py  # FastAPI middleware
```

### Archivos a modificar

- `src/config.py`: añadir settings de rate limit (§7).
- `src/main.py`: registrar middleware.
- `pyproject.toml`: tarea `redis` ya añadida en Fase 5.

### Detalle

#### `rate_limiter.py`

```python
@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime

class RateLimiter(Protocol):
    async def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult: ...
```

#### `redis_rate_limiter.py`

Sliding window con ZSET + script Lua atómico:
```lua
-- ZREMRANGEBYSCORE + ZADD + ZCARD en un solo round-trip
```

#### `memory_rate_limiter.py`

Fallback en memoria: `dict[str, list[float]]` con timestamps, poda por ventana. No es exacto entre workers pero protege la DB.

#### `rate_limit_middleware.py`

- Extrae `AuthContext` del request state (lo guarda `verify_api_key_dep`).
- Clave de tasa: `rl:{key_id}:{ventana}`.
- Parsea `SECURITY_RATE_LIMIT_DEFAULT` ("100/minute" → 100, 60).
- Aplica overrides por permiso (`SECURITY_RATE_LIMIT_OVERRIDES`).
- Si `allowed=False` → 429 + headers.
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`.

### Casos de uso

- **CU-6.1**: Request dentro del límite → pasa, headers con remaining.
- **CU-6.2**: Request excede límite → 429 + `Retry-After`.
- **CU-6.3**: Ventana deslizante: requests viejos expiran.
- **CU-6.4**: Override por permiso (ej. `users:write` → 10/min).
- **CU-6.5**: Redis cae → fallback memoria.
- **CU-6.6**: Rate limiting deshabilitado (`SECURITY_RATE_LIMIT_ENABLED=false`) → middleware no-op.

### Criterios de aceptación

- [ ] 429 con `Retry-After` y headers `X-RateLimit-*`.
- [ ] Sliding window con ZSET + Lua atómico.
- [ ] Límite por `key_id` (por API key).
- [ ] Overrides por permiso parseados desde config.
- [ ] Fallback a memoria si Redis no disponible.
- [ ] `SECURITY_RATE_LIMIT_ENABLED=false` → middleware no-op.
- [ ] Sin dependencias nuevas obligatorias (Redis ya en stack).
- [ ] `mypy --strict` y `ruff` limpios.

### Happy path

```bash
# Request 1-100 → 200
for i in $(seq 1 100); do
  curl -H "Authorization: Bearer pk_..." http://localhost:8000/api/v1/users/
done
# → 100 respuestas 200, headers: X-RateLimit-Remaining: 0

# Request 101 → 429
curl -H "Authorization: Bearer pk_..." http://localhost:8000/api/v1/users/
# → 429, Retry-After: 30, X-RateLimit-Reset: <timestamp>
```

### Sad path

```bash
# Redis cae → fallback memoria
# → requests siguen funcionando pero límites resetean por worker
# → log warning: "Redis unavailable, falling back to in-memory rate limiter"
```

---

## Fase 7 — Hardening: security headers, CORS, docs gating, request-id, audit log

**Objetivo:** Implementar las medidas de hardening transversal del §8 del req.

> **Paralelizable con Fase 1** (no toca los mismos archivos).

### Archivos a crear

```
src/shared/infrastructure/http/
├── security_headers_middleware.py   # X-Content-Type-Options, X-Frame-Options, etc.
├── request_id_middleware.py         # X-Request-ID generado o propagado
├── cors.py                          # CORS con whitelist por settings
└── audit_log.py                     # Log estructurado de operaciones de escritura
```

### Archivos a modificar

- `src/config.py`: `SECURITY_DOCS_PUBLIC: bool = True`, `CORS_ORIGINS: str = ""`.
- `src/main.py`: registrar middlewares, CORS, docs gating.
- `src/shared/infrastructure/http/error_handlers.py`: quitar log de `PG_HOST:PORT` en startup.

### Detalle

#### `security_headers_middleware.py`

Añade a toda respuesta:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Cache-Control: no-store` (en respuestas autenticadas, detectado por presencia de `AuthContext` en request state).
- `Strict-Transport-Security: max-age=31536000` (solo si TLS detectado).

#### `request_id_middleware.py`

- Lee `X-Request-ID` del request; si no viene, genera uno (`uuid4`).
- Lo añade a la respuesta.
- Lo pone en `request.state.request_id` para logs.

#### `cors.py`

- `CORS_ORIGINS` parsea JSON array o CSV desde settings.
- Si vacío → CORS deshabilitado.
- Si `*` → permitir todo (solo dev, warning en log).

#### `audit_log.py`

Middleware que loguea operaciones de escritura (POST/PUT/DELETE):
```json
{"request_id":"...","key_id":"...","name":"...","role":"...","method":"POST","path":"/api/v1/users/","status":201,"duration_ms":12}
```
Nunca loguea la raw key ni el header completo. Solo `key_prefix`.

#### Docs gating

En `create_app()`:
```python
docs_url = settings.DOCS_URL if settings.SECURITY_DOCS_PUBLIC else None
openapi_url = settings.OPENAPI_URL if settings.SECURITY_DOCS_PUBLIC else None
redoc_url = settings.REDOC_URL if settings.SECURITY_DOCS_PUBLIC else None
```

### Casos de uso

- **CU-7.1**: Toda respuesta tiene `X-Content-Type-Options: nosniff` y `X-Frame-Options: DENY`.
- **CU-7.2**: Respuesta autenticada tiene `Cache-Control: no-store`.
- **CU-7.3**: Request sin `X-Request-ID` → respuesta incluye uno generado.
- **CU-7.4**: Request con `X-Request-ID` → se propaga.
- **CU-7.5**: `SECURITY_DOCS_PUBLIC=false` → `/docs`, `/openapi.json`, `/redoc` devuelven 404.
- **CU-7.6**: CORS respeta whitelist de `CORS_ORIGINS`.
- **CU-7.7**: POST/PUT/DELETE genera audit log con `request_id`, `key_id`, `role`.

### Criterios de aceptación

- [ ] Headers de seguridad presentes en toda respuesta.
- [ ] `Cache-Control: no-store` en respuestas autenticadas.
- [ ] `X-Request-ID` generado/propagado en toda respuesta.
- [ ] `SECURITY_DOCS_PUBLIC=false` → docs 404.
- [ ] CORS respeta whitelist (no `*` en producción).
- [ ] Audit log estructurado en operaciones de escritura.
- [ ] Audit log nunca incluye raw key ni header completo.
- [ ] Sin stack traces en respuestas (problem+json).
- [ ] `mypy --strict` y `ruff` limpios.

### Happy path

```bash
curl -v http://localhost:8000/api/v1/users/?limit=1 \
  -H "Authorization: Bearer pk_..."
# Response headers:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Cache-Control: no-store
# X-Request-ID: <uuid>
```

### Sad path

```bash
# Docs deshabilitadas en producción
SECURITY_DOCS_PUBLIC=false
curl http://localhost:8000/docs
# → 404

# CORS rechaza origen no permitido
curl -H "Origin: https://evil.com" http://localhost:8000/api/v1/users/
# → sin header Access-Control-Allow-Origin
```

---

## Fase 8 — Plantillas GenCLI: routers nuevos nacen con `require_permission`

**Objetivo:** Actualizar los templates de GenCLI para que todo módulo nuevo nazca con protección de permisos, con un sufijo `--protected` / `--public` que indica si el UC requiere autenticación o no.

### Decisiones de diseño

1. **Sufijo de protección en comandos UC**: cada comando `--uc-*` acepta un flag opcional `--protected` (por defecto) o `--public`. Esto determina si el endpoint generado incluye `require_permission(...)` o no.
   - `--protected` (default): el endpoint incluye `Depends(require_permission(...))`.
   - `--public`: el endpoint no incluye `require_permission`. Útil para endpoints públicos (health, webhooks, callbacks).
2. **Router base `--hex`**: el router base **no** incluye `require_permission` a nivel router (para permitir mezclar endpoints públicos y protegidos). La protección se aplica **por endpoint**.
3. **Identificación visual**: los endpoints protegidos incluyen un comentario `# protected: <permission>` encima del decorator, y los públicos `# public`. Esto permite que `protect_module.py` / `unprotect_module.py` (Fase 9) los identifiquen y modifiquen.

### Archivos a modificar

- `.gen_cli/templates/hex/router_base_template.py`: importar `require_permission` (para que los scripts `register_uc_*` puedan referenciarlo sin import duplicado).
- `.gen_cli/scripts/register_uc_create.py`: añadir flag `--protected`/`--public`; POST incluye `require_permission("<snake_name>s:write")` si es protegido, o nada si es público.
- `.gen_cli/scripts/register_uc_update.py`: PUT → `require_permission("<snake_name>s:write")` o público.
- `.gen_cli/scripts/register_uc_delete.py`: DELETE → `require_permission("<snake_name>s:write")` o público.
- `.gen_cli/scripts/register_uc_get.py`: GET → `require_permission("<snake_name>s:read")` o público.
- `.gen_cli/scripts/register_uc_list.py`: GET → `require_permission("<snake_name>s:read")` o público.
- `.gen_cli/scripts/register_uc_list_paginated.py`: GET → `require_permission("<snake_name>s:read")` o público.
- `.gen_cli/scripts/register_uc_find_by.py`: POST → `require_permission("<snake_name>s:read")` o público.
- `src/modules/users/infrastructure/http/routers.py`: aplicar permisos a endpoints existentes.
- `doc/arquitectura.md`: documentar que todo router debe nacer con `require_permission` por defecto y el flag `--public` para excepciones.

### Detalle

#### Sufijo `--protected` / `--public` en comandos UC

El binario `gen` pasa el flag a los scripts `register_uc_*.py` via un argumento adicional. Ejemplo de invocación:

```bash
# Protegido (default)
./gen --uc-create User "nombre:str,email:str"
# → endpoint POST con require_permission("users:write")

# Público
./gen --uc-create Webhook "url:str" --public
# → endpoint POST sin require_permission
```

#### Marcadores en código generado

Cada endpoint generado incluye un comentario de marca para que `protect_module.py`/`unprotect_module.py` pueda identificar y modificar:

```python
# protected: users:write
@router.post("/", response_model=UserCreateResponse, status_code=201,
             dependencies=[Depends(require_permission("users:write"))])
async def create_users(...): ...
```

```python
# public
@router.post("/", response_model=WebhookCreateResponse, status_code=201)
async def create_webhooks(...): ...
```

#### `router_base_template.py` (modificado)

```python
from typing import Annotated

from fastapi import APIRouter, Depends

from src.modules.api_keys.infrastructure.http.auth_dependencies import require_permission

# gencli:router-imports


router = APIRouter(prefix="/<snake_name>s", tags=["<ent>s"])

# gencli:routes
```

#### Scripts `register_uc_*.py` (modificados)

Los scripts reciben un argumento adicional `protected: bool` (default `True`). Al generar el endpoint:

```python
if protected:
    endpoint = (
        f"# protected: {snake_name}s:{perm}\n"
        f"@router.{method}(..., dependencies=[Depends(require_permission(\"{snake_name}s:{perm}\"))])\n"
        f"async def {name}(...): ..."
    )
else:
    endpoint = (
        f"# public\n"
        f"@router.{method}(...)\n"
        f"async def {name}(...): ..."
    )
```

Donde `perm` es `"write"` para create/update/delete y `"read"` para get/list/find_by.

### Casos de uso

- **CU-8.1**: `gen --hex Product "name:str"` → router base sin protección a nivel router.
- **CU-8.2**: `gen --uc-create Product ...` (default) → endpoint POST con `# protected: products:write` + `require_permission`.
- **CU-8.3**: `gen --uc-create Webhook ... --public` → endpoint POST con `# public` sin `require_permission`.
- **CU-8.4**: `gen --uc-delete Product ...` (default) → endpoint DELETE con `# protected: products:write`.
- **CU-8.5**: Módulo `users` existente → rutas protegidas con permisos.

### Criterios de aceptación

- [ ] `--protected` es el comportamiento por defecto (sin flag explícito).
- [ ] `--public` genera endpoints sin `require_permission` y con marca `# public`.
- [ ] Endpoints protegidos incluyen comentario `# protected: <module>:<perm>`.
- [ ] Endpoints de escritura (create/update/delete) requieren `:write`.
- [ ] Endpoints de lectura (get/list/list_paginated/find_by) requieren `:read`.
- [ ] Smoke test de GenCLI valida que los routers generados incluyen `require_permission` cuando es protegido.
- [ ] Smoke test valida que `--public` genera sin `require_permission`.
- [ ] Test de arquitectura: un router sin `require_permission` y sin marca `# public` debe fallar.
- [ ] `mypy --strict` y `ruff` limpios.
- [ ] Suite completa de tests pasa.

### Happy path

```bash
# UC protegido (default)
./gen --uc-create Product "name:str,user:UUID,is_physical:bool"
# → endpoint con # protected: products:write + require_permission

# UC público
./gen --uc-list Health "status:str" --public
# → endpoint con # public, sin require_permission
```

### Sad path

```bash
# Request sin API key a un endpoint protegido
curl http://localhost:8000/api/v1/products/?limit=5
# → 401, WWW-Authenticate: Bearer

# Request sin API key a un endpoint público
curl http://localhost:8000/api/v1/healths/?limit=5
# → 200 (sin auth)

# Request con key de rol read intentando crear (protegido)
curl -X POST -H "Authorization: Bearer pk_read_only..." \
     -H "Content-Type: application/json" \
     -d '{"name":"Test"}' \
     http://localhost:8000/api/v1/products/
# → 403, "Acceso denegado"
```

---

## Fase 9 — GenCLI `--uc-delete-*`: eliminar UC + `protect_module.py` / `unprotect_module.py`

**Objetivo:** Dotar a cada comando `--uc-*` de un par `--uc-delete-*` que elimina **solo** los archivos generados por ese UC y limpia las referencias. Además, un script `protect_module.py` / `unprotect_module.py` que aplica o retira `require_permission` a un módulo existente sin regenerarlo.

### 9A — Comando `--uc-delete-*` por cada UC

Cada comando `--uc-*` tiene su contraparte `--uc-delete-*` que elimina exclusivamente los archivos que aquel generó:

| Comando de generación | Comando de eliminación | Archivos que elimina |
|---|---|---|
| `--uc-list` | `--uc-delete-list` | `use_cases/list_<ent>s.py`, `controllers/list_<ent>s_controller.py`, `tests/unit/modules/<ent>s/test_list_<ent>s.py` |
| `--uc-list-paginated` | `--uc-delete-list-paginated` | `use_cases/list_paginated_<ent>s.py`, `controllers/...`, `tests/...` |
| `--uc-find-by` | `--uc-delete-find-by` | `use_cases/find_by_<ent>s.py`, `controllers/...`, `tests/...` |
| `--uc-create` | `--uc-delete-create` | `use_cases/create_<ent>s.py`, `controllers/...`, `tests/...` |
| `--uc-get` | `--uc-delete-get` | `use_cases/get_<ent>s.py`, `controllers/...`, `tests/...` |
| `--uc-update` | `--uc-delete-update` | `use_cases/update_<ent>s.py`, `controllers/...`, `tests/...` |
| `--uc-delete` | `--uc-delete-delete` | `use_cases/delete_<ent>s.py`, `controllers/...`, `tests/...` |

#### Archivos a crear

```
.gen_cli/scripts/
├── delete_uc_list.py
├── delete_uc_list_paginated.py
├── delete_uc_find_by.py
├── delete_uc_create.py
├── delete_uc_get.py
├── delete_uc_update.py
└── delete_uc_delete.py
```

#### Archivos a modificar

- `arq.json`: añadir 7 entradas nuevas, una por cada `--uc-delete-*`, con sus templates (ninguno — solo ejecutan el script `onDone`).

```json
{
  "name": "hex use case delete list",
  "path": "/src/modules/<snake_name>s",
  "short_option": "-L",
  "option": "--uc-delete-list",
  "description": "Elimina el caso de uso de listado y limpia referencias",
  "has_props": true,
  "prop_type_separator": ":",
  "prop_prop_place": 1,
  "prop_type_place": 2,
  "prop_prefix": null,
  "templates": [
    {
      "template": "/hex/.no_op",
      "destination": "<path>/.no_op",
      "onDone": "python .gen_cli/scripts/delete_uc_list.py <destination> <ent> <snake_name> \"<inline_props>\""
    }
  ]
}
```

> **Nota:** GenCLI requiere al menos un template por entrada. Se usa un archivo `.no_op` vacío como placeholder que el script elimina inmediatamente.

#### Detalle del script `delete_uc_*.py`

Cada script sigue el mismo patrón:

```python
def delete_uc(generated_file: Path, entity_name: str, snake_name: str) -> None:
    """Elimina los archivos del UC y limpia referencias en router/dependencies/schemas."""
    module_root = _find_module_root(generated_file.resolve())
    plural_name = f"{snake_name}s"

    # 1. Archivos a eliminar
    files_to_delete = [
        module_root / "use_cases" / f"list_{plural_name}.py",
        module_root / "infrastructure" / "http" / "controllers" / f"list_{plural_name}_controller.py",
        project_root / "tests" / "unit" / "modules" / plural_name / f"test_list_{plural_name}.py",
    ]

    # 2. Limpiar referencias en router.py (remover import + endpoint)
    router_path = module_root / "infrastructure" / "http" / "routers.py"
    # - Remover: from .controllers.list_{plural_name}_controller import ...
    # - Remover: from ...dependencies import get_list_{plural_name}
    # - Remover: from ...use_cases.list_{plural_name} import List{plural_entity}
    # - Remover: @router.get(...) + async def list_{plural_name}(...)

    # 3. Limpiar referencias en dependencies.py (remover import + provider)
    # - Remover: from ...use_cases.list_{plural_name} import List{plural_entity}
    # - Remover: def get_list_{plural_name}(...): ...

    # 4. Limpiar referencias en schemas.py (remover schemas + mappers del UC)
    # - Detectar y remover solo los schemas/mappers que pertenecen a este UC

    # 5. Eliminar archivos físicos
    for f in files_to_delete:
        if f.is_file():
            f.unlink()

    # 6. Validar que los archivos modificados siguen siendo Python válido
    _write_atomically(documents)
```

#### Limpieza de referencias — estrategia

La limpieza de `router.py`, `dependencies.py` y `schemas.py` usa **bloques delimitados**. Cada UC inserta su código con un prefijo identificable:

- **Router**: el endpoint + sus imports se identifican por el nombre de la función (`list_{plural_name}`, `create_{plural_name}`, etc.).
- **Dependencies**: el provider se identifica por `def get_{uc_name}_{plural_name}(`.
- **Schemas**: los schemas se identifican por nombres de clase (`{Entity}{UC}Request`, `{Entity}{UC}Response`, etc.).

El script usa regex para remover:
1. La línea `from ...import` que referencia el controller/use_case/dependency del UC.
2. El bloque `@router.{method}(...)` + `async def {uc}_{plural_name}(...)` completo.
3. El bloque `def get_{uc}_{plural_name}(...): ...` en dependencies.
4. Los schemas cuyos nombres contienen el identificador del UC.

#### Casos de uso

- **CU-9.1**: `gen --uc-delete-create User "nombre:str,email:str"` → elimina `create_users.py`, `create_users_controller.py`, `test_create_users.py` + limpia router/dependencies/schemas.
- **CU-9.2**: `gen --uc-delete-list Product ...` → elimina archivos de list + limpia.
- **CU-9.3**: Eliminar un UC que no existe → error claro: "El caso de uso 'list' no existe en el módulo 'users'".
- **CU-9.4**: Eliminar un UC y re-generarlo → el módulo queda idéntico.
- **CU-9.5**: Eliminar un UC no afecta a los demás UCs del módulo.

#### Criterios de aceptación

- [ ] Cada `--uc-delete-*` elimina exclusivamente los archivos de ese UC.
- [ ] Las referencias en `router.py`, `dependencies.py` y `schemas.py` se limpian.
- [ ] Los archivos restantes siguen siendo Python válido (`ast.parse`).
- [ ] Eliminar un UC inexistente produce un error claro (no crash).
- [ ] Eliminar y re-generar un UC produce el mismo resultado.
- [ ] `mypy --strict` y `ruff` limpios tras eliminar cualquier UC.
- [ ] Smoke test: generar todos los UCs, eliminar uno, validar que el resto funciona.

#### Happy path

```bash
# Generar módulo completo
./gen --hex User "nombre:str,email:str"
./gen --uc-create User "nombre:str,email:str"
./gen --uc-get User "nombre:str,email:str"
./gen --uc-list User "nombre:str,email:str"

# Eliminar solo el UC create
./gen --uc-delete-create User "nombre:str,email:str"
# → Archivos eliminados: create_users.py, create_users_controller.py, test_create_users.py
# → Referencias removidas de router.py, dependencies.py, schemas.py

# Los UCs get y list siguen funcionando
curl -H "Authorization: Bearer pk_..." http://localhost:8000/api/v1/users/?limit=5
# → 200
curl -H "Authorization: Bearer pk_..." http://localhost:8000/api/v1/users/{id}
# → 200

# El endpoint create ya no existe
curl -X POST -H "Authorization: Bearer pk_..." http://localhost:8000/api/v1/users/
# → 404
```

#### Sad path

```bash
# Eliminar UC que no existe
./gen --uc-delete-create Product "name:str"
# → Error: El caso de uso 'create' no existe en el módulo 'products'

# Eliminar UC de módulo que no existe
./gen --uc-delete-list Nonexistent "name:str"
# → Error: No existe el módulo 'nonexistents'
```

---

### 9B — Script `protect_module.py` / `unprotect_module.py`

**Objetivo:** Permitir aplicar o retirar `require_permission` a todos los endpoints de un módulo existente sin regenerarlos.

#### Archivos a crear

```
.gen_cli/scripts/
├── protect_module.py
└── unprotect_module.py
```

#### `arq.json`

```json
{
  "name": "protect module",
  "path": "/src/modules/<snake_name>s",
  "short_option": "P",
  "option": "--protect",
  "description": "Aplica require_permission a todos los endpoints públicos del módulo",
  "has_props": false,
  "templates": [
    {
      "template": "/hex/.no_op",
      "destination": "<path>/.no_op",
      "onDone": "python .gen_cli/scripts/protect_module.py <destination> <ent> <snake_name>"
    }
  ]
},
{
  "name": "unprotect module",
  "path": "/src/modules/<snake_name>s",
  "short_option": "U",
  "option": "--unprotect",
  "description": "Retira require_permission de todos los endpoints del módulo",
  "has_props": false,
  "templates": [
    {
      "template": "/hex/.no_op",
      "destination": "<path>/.no_op",
      "onDone": "python .gen_cli/scripts/unprotect_module.py <destination> <ent> <snake_name>"
    }
  ]
}
```

#### Detalle de `protect_module.py`

```python
def protect_module(router_path: Path, snake_name: str) -> None:
    """Aplica require_permission a todos los endpoints marcados como # public."""
    content = router_path.read_text(encoding="utf-8")

    # 1. Asegurar que el import de require_permission existe
    if "require_permission" not in content:
        # Insertar import después de # gencli:router-imports
        ...

    # 2. Para cada endpoint marcado # public:
    #    - Reemplazar "# public" por "# protected: <module>:<perm>"
    #    - Añadir dependencies=[Depends(require_permission("<module>:<perm>"))]
    #    - Determinar perm: "write" si POST/PUT/DELETE, "read" si GET

    # 3. Validar con ast.parse
    _write_atomically({router_path: content})
```

#### Detalle de `unprotect_module.py`

```python
def unprotect_module(router_path: Path, snake_name: str) -> None:
    """Retira require_permission de todos los endpoints marcados como # protected."""
    content = router_path.read_text(encoding="utf-8")

    # 1. Para cada endpoint marcado # protected: <module>:<perm>:
    #    - Reemplazar "# protected: ..." por "# public"
    #    - Remover dependencies=[Depends(require_permission(...))] del decorator

    # 2. Si no quedan endpoints protegidos, remover el import de require_permission

    # 3. Validar con ast.parse
    _write_atomically({router_path: content})
```

#### Detección de permiso por método HTTP

```python
WRITE_METHODS = {"post", "put", "delete"}
perm = "write" if method in WRITE_METHODS else "read"
```

#### Casos de uso

- **CU-9B.1**: `gen --protect User` → todos los endpoints `# public` del módulo users pasan a `# protected: users:<perm>` con `require_permission`.
- **CU-9B.2**: `gen --unprotect User` → todos los endpoints `# protected` pasan a `# public` sin `require_permission`.
- **CU-9B.3**: `gen --protect` sobre un módulo ya protegido → no-op (todos ya están protegidos).
- **CU-9B.4**: `gen --unprotect` sobre un módulo ya público → no-op.
- **CU-9B.5**: Proteger un módulo y luego desprotegerlo → el router queda idéntico al original.

#### Criterios de aceptación

- [ ] `--protect` convierte todos los `# public` en `# protected` con `require_permission`.
- [ ] `--unprotect` convierte todos los `# protected` en `# public` sin `require_permission`.
- [ ] El permiso asignado es `:write` para POST/PUT/DELETE y `:read` para GET.
- [ ] Proteger un módulo ya protegido es no-op.
- [ ] Desproteger un módulo ya público es no-op.
- [ ] Proteger + desproteger deja el router idempotente.
- [ ] Si no quedan endpoints protegidos tras `--unprotect`, el import de `require_permission` se remueve.
- [ ] `mypy --strict` y `ruff` limpios tras proteger/desproteger.
- [ ] Smoke test: generar módulo público, proteger, validar 401 sin key, desproteger, validar 200 sin key.

#### Happy path

```bash
# Generar módulo público
./gen --hex Webhook "url:str"
./gen --uc-create Webhook "url:str" --public
./gen --uc-list Webhook "url:str" --public

# Sin auth → funciona
curl http://localhost:8000/api/v1/webhooks/?limit=5
# → 200

# Proteger el módulo
./gen --protect Webhook
# → Endpoints ahora tienen # protected: webhooks:read/write + require_permission

# Sin auth → 401
curl http://localhost:8000/api/v1/webhooks/?limit=5
# → 401

# Con auth → 200
curl -H "Authorization: Bearer pk_..." http://localhost:8000/api/v1/webhooks/?limit=5
# → 200

# Desproteger
./gen --unprotect Webhook
# → Endpoints vuelven a # public sin require_permission

# Sin auth → 200
curl http://localhost:8000/api/v1/webhooks/?limit=5
# → 200
```

#### Sad path

```bash
# Proteger módulo inexistente
./gen --protect Nonexistent
# → Error: No existe el módulo 'nonexistents'

# Proteger módulo ya protegido
./gen --protect User  # (users ya está protegido)
# → "El módulo 'users' ya tiene todos sus endpoints protegidos. No-op."
```

---

## Dependencias entre fases

```
F1 ──→ F2 ──→ F3 ──→ F4 ──→ F8 ──→ F9
                │              ↑
                ├──→ F5        │
                ├──→ F6        │
                └──────────────┘
F7 (paralelo con F1)
```

- **F1** es prerrequisito de todo el módulo (dominio + cripto).
- **F2** construye sobre F1 (use cases + adapter).
- **F3** construye sobre F2 (HTTP adapter).
- **F4** refina F3 (AccessPolicy).
- **F5** y **F6** son independientes entre sí, ambas requieren F3.
- **F7** no tiene dependencias del módulo (hardening transversal).
- **F8** requiere F3 y F4 (templates usan `require_permission` + flag `--public`).
- **F9** requiere F8 (los marcadores `# protected`/`# public` deben existir en los templates).

## Estimación por fase

| Fase | Complejidad | Líneas aprox. | Tests aprox. |
|------|-------------|---------------|--------------|
| 1 | Media | ~250 | 8-10 |
| 2 | Alta | ~400 | 12-15 |
| 3 | Alta | ~350 | 10-12 |
| 4 | Baja | ~100 | 8-10 |
| 5 | Media | ~200 | 8-10 |
| 6 | Alta | ~300 | 10-12 |
| 7 | Media | ~200 | 8-10 |
| 8 | Media | ~150 (modifs) | 8-10 |
| 9 | Alta | ~500 | 15-20 |

**Total estimado:** ~2450 líneas + ~85-105 tests → **~9 días** con un implementador, **~6 días** con dos en paralelo (F1+F7, luego F2, F3, F4+F5+F6 en paralelo, F8, F9).