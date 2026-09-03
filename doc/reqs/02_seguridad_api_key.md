# REQS-02 · Módulo de Seguridad — API Key, autorización y hardening OWASP

> **Estado:** Propuesto · **Prioridad:** Alta · **Depende de:** REQS-01 (hereda puertos, use cases, composition root y error handlers)
> **Alcance:** Módulo `api_keys` hexagonal, protección de rutas, autorización por roles (evolutiva a scopes), rate limiting propio y hardening OWASP API Security Top 10.

---

## 1. Objetivo

Proveer al microservicio un módulo de seguridad que:

1. Autentique clientes mediante **API Keys** con los más altos estándares (generación, almacenamiento hasheado, comparación constant-time, rotación, revocación, expiración).
2. Proteja rutas mediante **roles** (entrega 1) con una frontera de diseño que permita evolucionar a **scopes granulares** (entrega 2) sin tocar routers ni use cases.
3. Mitigue los riesgos del **OWASP API Security Top 10** (categorías vigentes, consistentes con el borrador 2026) de forma medible y testeable.

## 2. Decisiones tomadas

| # | Decisión | Elección |
|---|---|---|
| 1 | Ubicación de API keys | **Módulo propio** `src/modules/api_keys/` (es dominio de negocio con ciclo de vida propio) |
| 2 | Estrategia de lookup de claves | **Ambas**, seleccionable por `.env`: `postgres` (directo) o `redis_cache` (Postgres + caché Redis) |
| 3 | Header de transporte | Ver §5 (pros/cons) — se recomienda `Authorization: Bearer`; extracción aislada en una sola función |
| 4 | Modelo de autorización | **Roles** ahora; **scopes granulares** en entrega futura; frontera de intercambio definida en §6 |
| 5 | Rate limiting | **Implementación propia** (sliding window sobre Redis, fallback en memoria) — sin dependencias externas |

## 3. Diseño del módulo `api_keys` (hexagonal)

```
src/modules/api_keys/
├── domain/
│   ├── entities.py              # ApiKeyEntity: id, name, key_prefix, key_hash, role,
│   │                            #   status, expires_at, revoked_at, created_at, last_used_at
│   ├── value_objects.py         # RawApiKey (solo en RAM), KeyHash, KeyPrefix, KeyStatus
│   ├── repositories.py          # PUERTO: ApiKeyRepository (find_by_prefix, save, revoke...)
│   ├── services.py              # PUERTO: KeyHasher (hash, verify)  ← criptografía intercambiable
│   └── exceptions.py            # InvalidApiKeyError, ExpiredApiKeyError, RevokedApiKeyError,
│                                #   InsufficientRoleError
├── use_cases/
│   ├── verify_api_key.py        # Núcleo: raw key → ApiKeyEntity validada (o excepción de dominio)
│   ├── create_api_key.py        # Genera raw key, devuelve (entity, raw) — raw se muestra UNA vez
│   ├── rotate_api_key.py        # Nuevo secret, mismo id/name/role
│   └── revoke_api_key.py
└── infrastructure/
    ├── http/
    │   ├── api_key_header.py    # Extracción del header (ÚNICO punto si cambia §5)
    │   ├── auth_dependencies.py # verify_api_key_dep, require_role(...)  ← lo que consumen los routers
    │   ├── routers.py           # CRUD de api_keys (protegido con rol admin)
    │   ├── schemas.py
    │   ├── controllers/
    │   └── dependencies.py      # Composition root del módulo
    └── persistence/
        ├── models.py            # Tabla api_keys
        ├── repositories.py      # PostgresApiKeyRepository (implementa el puerto)
        └── cached_repository.py # CachedApiKeyRepository: DECORADOR sobre el de Postgres (estrategia §4)
scripts/
└── create_api_key.py            # CLI de emisión (patrón create_table): imprime la raw key una sola vez
```

### 3.1 Esquema de tabla `api_keys`

```sql
CREATE TABLE api_keys (
    id            UUID PRIMARY KEY,                    -- uuid7
    name          VARCHAR(100) NOT NULL UNIQUE,        -- identificación humana del cliente
    key_prefix    VARCHAR(12)  NOT NULL,               -- p.ej. "pk_a1b2c3d4"; indexado
    key_hash      VARCHAR(64)  NOT NULL,               -- HMAC-SHA256 hex (64 chars)
    role          VARCHAR(20)  NOT NULL,               -- "admin" | "write" | "read"  (§6)
    status        VARCHAR(10)  NOT NULL DEFAULT 'active',  -- active | revoked
    expires_at    TIMESTAMPTZ,
    revoked_at    TIMESTAMPTZ,
    last_used_at  TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX ix_api_keys_prefix ON api_keys (key_prefix) WHERE status = 'active';
```

### 3.2 Diseño de la clave (estándar de industria)

| Aspecto | Decisión | Riesgo que mitiga |
|---|---|---|
| Formato | `pk_<8 chars de id>_<secret 43 chars>` → `pk_a1b2c3d4_Xy...` | Identificación O(1) por índice sin escanear la tabla |
| Entropía | `secrets.token_urlsafe(32)` (≥256 bits) | Fuerza bruta |
| Almacenamiento | **Nunca en claro**: `HMAC-SHA256(raw_secret, pepper)` con `SECURITY_PEPPER` (≥32 bytes, en `.env`/secrets manager). Alternativa futura sin cambio de interfaz: Argon2id (puerto `KeyHasher`) | Fuga por dump de DB |
| Comparación | `hmac.compare_digest` (constant-time) | Timing attacks |
| Visualización | Raw key se devuelve **una sola vez** en creación/rotación; luego solo `key_prefix` | Exposición permanente |
| Expiración | `expires_at` opcional por clave | Claves eternas |
| `last_used_at` | Actualizado **async/batched** (no un UPDATE por request) | Cuello de botella de escritura |

### 3.3 Flujo de verificación

```
Request → extraer header (api_key_header.py)
        → parsear prefijo + secret
        → ApiKeyRepository.find_by_prefix(prefijo)      [estrategia §4]
        → KeyHasher.verify(secret, key_hash)  (constant-time)
        → validar status/expiración
        → retornar AuthContext(key_id, name, role)
   401  → ausente/malformada/inválida/expirada/revocada  + WWW-Authenticate
   403  → clave válida pero rol insuficiente
```

`AuthContext` es un objeto de dominio ligero (`shared/domain/auth_context.py`) que viaja hacia los use cases: es la semilla para mitigar BOLA (API1) en módulos futuros.

## 4. Estrategia de lookup: ambas, configurable (Decisión 2)

Patrón **Decorator**: `CachedApiKeyRepository` envuelve a `PostgresApiKeyRepository`. `verify_api_key` no sabe cuál está activa — el composition root decide según settings.

```env
# .env — selección de estrategia
SECURITY_KEY_LOOKUP=postgres      # postgres | redis_cache
SECURITY_KEY_CACHE_TTL=60         # segundos (solo redis_cache)
SECURITY_KEY_CACHE_NEG_TTL=10     # caché de "no existe" anti-enumeración
```

| | `postgres` | `redis_cache` |
|---|---|---|
| Latencia | 1 query por request | ~sub-ms tras primer hit |
| Consistencia de revocación | **Inmediata** | Hasta expirar TTL (≤60s) |
| Dependencia | Solo Postgres | Postgres + Redis |
| Uso recomendado | Dev / compliance estricto | Producción de alto tráfico |

**Invalidación activa**: `revoke_api_key`/`rotate_api_key` borran la entrada de caché por `key_prefix` (revocación efectiva en segundos, no al expirar TTL). En `postgres` Redis no se toca. Falla de Redis → degradar a Postgres + log de warning (fail-open a la DB, nunca fail-open a permitir acceso).

## 5. Header de transporte: pros y cons (Decisión 3)

| | `Authorization: Bearer <key>` | `X-API-Key: <key>` |
|---|---|---|
| **Pros** | Estándar RFC 6750; proxies/gateways/middleware lo tratan de forma nativa; camino natural a JWT/OAuth sin cambiar consumidores; librerías HTTP lo manejan por defecto | Semántica explícita ("esto es una API key"); no hay confusión con tokens Bearer de terceros; trivial de filtrar en logs/apm por nombre |
| **Contras** | En sistemas mixtos podría confundirse con un JWT | No estándar; cada gateway requiere regla custom; si mañana se agrega JWT coexistirían dos mecanismos |
| Infraestructura | Reconocido universalmente | Configuración manual en cada proxy/WAF |
| OpenAPI | `securitySchemes: bearer` soportado nativamente (candado en Swagger UI) | Requiere `apiKey` custom |

**Recomendación: `Authorization: Bearer`.** La extracción vive exclusivamente en `api_key_header.py` (una función), por lo que soportar `X-API-Key` en el futuro (o ambos, configurables) es un cambio de un archivo sin tocar routers ni use cases. `SECURITY_API_KEY_HEADER=bearer|x-api-key` en `.env` como evolución barata si se necesitara.

**Regla dura**: la clave nunca viaja en query string ni en la URL (queda en access logs, historial, proxies). OpenAPI documentará la cookie de seguridad global para todas las rutas protegidas.

## 6. Autorización: roles ahora, scopes después (Decisión 4)

### 6.1 Frontera de intercambio

La pieza que evoluciona es **quién resuelve permisos**, no quién los exige. Se define un solo puerto:

```python
# shared/domain/access_policy.py
class AccessPolicy(Protocol):
    def can(self, ctx: AuthContext, required: Permission) -> bool: ...
```

- `Permission` = `NewType(str)` con formato de ruta jerárquica: `"users:read"`, `"users:write"`, `"api_keys:admin"`.
- **Los routers declaran permisos y no cambian nunca**: `require_permission("users:read")`.
- La **implementación** del `AccessPolicy` es la que se sustituye entre entregas.

### 6.2 Entrega 1 — Roles

```python
# modules/api_keys/domain/role_policy.py
ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "admin": frozenset({"*"}),                    # todo, incluida gestión de claves
    "write": frozenset({"*:read", "*:write"}),    # CRUD de negocio, no gestión de claves
    "read":  frozenset({"*:read"}),
}
```

`RoleAccessPolicy.can(ctx, required)` consulta el mapa. Nuevos roles = agregar entradas al mapa, cero cambios estructurales.

### 6.3 Entrega 2 — Scopes granulares (diseñado, no implementado)

1. Migración: columna `role VARCHAR` → conservarla y **agregar** `scopes TEXT[] NULL`; `NULL` = "usar rol" (retrocompatible).
2. Nueva implementación `ScopeAccessPolicy` que resuelve contra `scopes` cuando existe, con fallback a `RoleAccessPolicy` si no.
3. `create_api_key`/`rotate` aceptan scopes opcionales; la tabla y el flujo de verificación no cambian.
4. `verify_api_key` ya carga toda la fila → `AuthContext` incorpora `scopes` sin tocar routers.

**Costo de la evolución**: 1 migración aditiva + 1 clase nueva + 1 línea en el composition root. Routers, use cases y tests de permisos intactos.

### 6.4 Uso en routers (contrato público estable)

```python
router = APIRouter(
    prefix="/users", tags=["Users"],
    dependencies=[Depends(require_permission("users:read"))],   # a nivel router
)
# o por endpoint para mezclar lectura/escritura
@router.post("/", dependencies=[Depends(require_permission("users:write"))])
```

## 7. Rate limiting propio (Decisión 5)

Sin dependencias externas: token/sliding window implementado con Lua atómica sobre Redis.

```env
SECURITY_RATE_LIMIT_ENABLED=true
SECURITY_RATE_LIMIT_ALGO=sliding_window   # sliding_window | fixed_window
SECURITY_RATE_LIMIT_DEFAULT=100/minute    # sintaxis "<n>/<unidad>"
SECURITY_RATE_LIMIT_OVERRIDES={"users:write":"10/minute"}
SECURITY_RATE_LIMIT_BACKEND=redis         # redis | memory (fallback auto si Redis cae)
```

- **Clave de tasa**: `rl:{key_id}:{ventana}` — límites **por API key** (por-key_id), base para tiers futuros.
- **Sliding window** con ZSET (`ZADD/ZREMRANGEBYSCORE/ZCARD` en script Lua atómico).
- **Respuestas estándar**: `429` + `Retry-After` + headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
- **Fallback**: si Redis no disponible → ventana en memoria por proceso + warning (protege la DB, con degradación documentada en multi-worker).
- Punto de extensión declarado: tier por clave (`rate_tier`) en tabla para límites diferenciados — fuera de alcance de esta entrega.

## 8. Hardening transversal (OWASP API Security Top 10)

| # | Categoría OWASP | Medida en este diseño |
|---|---|---|
| API1 | BOLA (Object Level Authz) | `AuthContext` disponible en use cases; regla de plantilla: todo endpoint con id en ruta debe filtrar por ownership en el repositorio. En este template: documentado + patrón listo |
| API2 | Broken Authentication | Módulo completo (§3): hash+pepper, constant-time, expiración, revocación, rotación |
| API3 | Property Level Authz | Schemas de respuesta explícitos (nunca `orm_mode` sobre entidades crudas); `api_keys` nunca devuelve `key_hash` |
| API4 | Unrestricted Resource Consumption | Rate limit (§7) + **tope de paginación `le=100`** en todos los `limit` + límite de tamaño de body en el servidor ASGI |
| API5 | BFLA (Function Level Authz) | Permiso obligatorio por router/endpoint (§6.4); gestión de api_keys solo `admin` |
| API6 | Sensitive Business Flows | Overrides de rate limit por operación sensible (§7) |
| API7 | SSRF | Sin fetch de URLs del cliente en esta entrega; regla documentada para integraciones futuras (Meilisearch/Rabbit: URLs solo desde settings, nunca del request) |
| API8 | Security Misconfiguration | CORS whitelist por settings; **docs/redoc/openapi deshabilitados en producción** (`SECURITY_DOCS_PUBLIC=false`); DEBUG off; sin stack traces (problem+json); quitar log de `PG_HOST:PORT` en startup |
| API9 | Improper Inventory | `/health` incluye versión+entorno; OpenAPI como inventario; tags por módulo |
| API10 | Unsafe Consumption | Integraciones futuras deben validar respuesta upstream con schemas Pydantic antes de usarla (regla de plantilla) |

### Middleware y handlers (shared)

- **Security headers** (middleware propio, configurable): `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Cache-Control: no-store` (en respuestas autenticadas), `Strict-Transport-Security` cuando TLS activo.
- **Request ID**: `X-Request-ID` (generado si no viene) para correlación en logs.
- **Audit log**: por operación de escritura → línea estructurada `{request_id, key_id, name, role, method, path, status, duration_ms}`. Nunca loguear la raw key ni el header completo (loguear solo `key_prefix`).
- **Problem+json (RFC 9457)** para todos los errores (heredado de REQS-01); errores 401/403/429 con mensajes sin filtrar existencia de claves ajenas.

## 9. Configuración nueva (resumen `.env`)

```env
# --- API Keys ---
SECURITY_PEPPER=<32+ bytes aleatorios, requerido>
SECURITY_KEY_LOOKUP=postgres            # postgres | redis_cache
SECURITY_KEY_CACHE_TTL=60
SECURITY_KEY_CACHE_NEG_TTL=10

# --- Autorización ---
# (roles fijos en código; sin config en entrega 1)

# --- Rate limiting ---
SECURITY_RATE_LIMIT_ENABLED=true
SECURITY_RATE_LIMIT_BACKEND=redis
SECURITY_RATE_LIMIT_DEFAULT=100/minute

# --- Hardening ---
SECURITY_DOCS_PUBLIC=false              # en producción: docs/openapi fuera
CORS_ORIGINS=["https://app.midominio.com"]
```

Cambios en `src/config.py`: agrupar como propiedades opcionales los settings no usados hoy (`MS_*`, `MEILISEARCH_*`) para no forzar dummy secrets.

## 10. Plan de implementación

| Fase | Entregable |
|---|---|
| 1 | Migración `api_keys` + dominio (entidad, VOs, puertos, excepciones) + `KeyHasher` HMAC |
| 2 | Use cases (create/verify/rotate/revoke) + Postgres adapter + CLI `create_api_key` |
| 3 | HTTP adapter: header extractor, `verify_api_key_dep`, `require_permission`, `AuthContext`; proteger `users`/`products` |
| 4 | `RoleAccessPolicy` + tests de la matriz de permisos |
| 5 | Estrategia `redis_cache` (decorador) + invalidación activa + fallback |
| 6 | Rate limiter propio (Lua/sliding window) + headers 429 + fallback memoria |
| 7 | Hardening: security headers, CORS, docs gating, request-id, audit log |
| 8 | Plantillas GenCLI: routers nuevos nacen con `require_permission(...)`; doc de módulo actualizada |

## 11. Matriz de pruebas

| Grupo | Casos |
|---|---|
| Unit — cripto | hash determinista con pepper; verify true/false; raw keys únicas; formatos malformados |
| Unit — verify use case | válida / inexistente / expirada / revocada / pepper distinto → excepciones de dominio correctas |
| Unit — AccessPolicy | cada rol × cada permiso; wildcard `*` y `*:read`; rol desconocido → denegar |
| Integración — cache | hit/miss/invalidación en revoke/rotate; TTL; caída de Redis → fallback Postgres |
| Unit — rate limiter | límite exacto; ventana deslizante; overrides; fallback memoria; headers correctos |
| E2E — auth | sin header→401; key inválida→401; rol insuficiente→403; flujo CRUD de claves; revocación surte efecto |
| E2E — seguridad | docs 404 en prod; `limit=10000`→422; headers de seguridad presentes; request-id propagado |
| Timing | verificación con clave inexistente vs inválida: diferencia de tiempo no explotable (comparación constant-time tras lookup) |

## 12. Criterios de aceptación

- [ ] Ninguna raw key persiste en claro (ni DB, ni logs, ni respuestas posteriores a la creación).
- [ ] Verificación constant-time; lookup por prefijo indexado.
- [ ] Revocación efectiva ≤ TTL de caché y en segundos con invalidación activa.
- [ ] Toda ruta de negocio exige permiso explícito; un router sin `require_permission` debe fallar en review/test de arquitectura.
- [ ] Cambiar `SECURITY_KEY_LOOKUP` no requiere cambios de código.
- [ ] Entrega 2 (scopes) requiere solo: migración aditiva + `ScopeAccessPolicy` + 1 línea de composition root.
- [ ] 429 con `Retry-After` y headers `X-RateLimit-*`.
- [ ] Sin dependencias nuevas obligatorias (Redis ya es parte del stack vía config; el fallback memoria cubre su ausencia).

## 13. Fuera de alcance (entregas futuras)

- Scopes granulares por clave (§6.3 — diseñado, no implementado).
- Tiers de rate limit por clave y cuotas mensuales.
- JWT/OAuth2 para usuarios finales (la extracción por header ya deja el camino preparado).
- mTLS, IP allowlisting, WAF.
- Alerting/SIEM sobre audit log.
