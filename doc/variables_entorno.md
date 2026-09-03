# Variables de entorno para DevOps

Guía de referencia de cada variable de entorno que el microservicio lee al
arrancar. Está pensada para que un equipo DevOps / SRE pueda construir el
`.env` o inyectar las variables en el orquestador (Docker Compose, Kubernetes,
ECS, etc.) sin tener que leer el código fuente.

Las variables se cargan con `pydantic-settings`, que lee en este orden de
prioridad (de mayor a menor):

1. Variables de entorno del sistema operativo (las que inyecta el orquestador).
2. Archivo `.env` en la raíz del proyecto (si existe).
3. Valor por defecto declarado en `src/config.py`.

> **Regla de oro**: si una variable del SO existe, **ignora** la del `.env`.
> Esto significa que en producción basta con inyectar variables en el
> contenedor y no se necesita un `.env` dentro de la imagen.

El archivo `.env` está en `.gitignore` y nunca debe subirse al repositorio.
El archivo `.env.example` (que sí está versionado) sirve como plantilla con
todos los nombres y comentarios, pero con valores vacíos.

## Índice rápido

| Sección | Variables | Obligatorias en producción |
|---|---|---|
| [Origen de datos](#repository_data_source) | `REPOSITORY_DATA_SOURCE` | Sí |
| [Configuración base](#configuracion-base) | `APP_NAME`, `ENVIRONMENT`, `DEBUG`, `API_VERSION`, `API_DESCRIPTION` | `APP_NAME`, `ENVIRONMENT` |
| [Documentación OpenAPI](#documentacion-openapi) | `OPENAPI_URL`, `DOCS_URL`, `REDOC_URL` | En producción se recomienda deshabilitar |
| [PostgreSQL](#postgresql) | `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_PORT`, `PG_DB`, `PG_SSLMODE`, `PG_CONNECT_TIMEOUT` | Sí, si `REPOSITORY_DATA_SOURCE=database` |
| [SQL Server](#sql-server) | `MS_USER`, `MS_PASSWORD`, `MS_HOST`, `MS_PORT`, `MS_DB` | Solo si se integra con SQL Server |
| [Mensajería y caché](#mensajeria-y-cache) | `RABBITMQ_URL`, `REDIS_URL` | Si se usan |
| [Seguridad (API Keys)](#seguridad-api-keys) | `SECURITY_PEPPER` | Sí, si `REPOSITORY_DATA_SOURCE=database` |
| [Paginación keyset](#paginacion-keyset) | `PAGINATION_CURSOR_SECRET` | Sí, si `REPOSITORY_DATA_SOURCE=database` |
| [Búsqueda (Meilisearch)]#busqueda-meilisearch) | `MEILISEARCH_URL`, `MEILISEARCH_MASTER_KEY` | Si se usa Meilisearch |

---

## REPOSITORY_DATA_SOURCE

**Tipo**: enumerado (string) — `database` | `faker`
**Por defecto**: `database`
**Obligatoria**: sí

Controla de dónde obtiene el servicio los datos. Es la variable más importante
del arranque porque determina qué adaptador de persistencia se inyecta en
cada petición y qué bloques del ciclo de vida (`lifespan`) se ejecutan.

### `database`

Usa **PostgreSQL** real mediante SQLAlchemy + asyncpg. La aplicación:

- Abre un motor (engine) asíncrono al arrancar con las credenciales de `PG_*`.
- Verifica la conectividad con un *ping*; si falla, reintenta hasta 5 veces
  con *backoff* de 2 segundos entre intentos. Si todas fallan, el proceso
  aborta con error explícito.
- Inyecta `SqlAlchemyUnitOfWork` (sesión de DB por petición) a los casos de
  uso.
- **Requiere** que `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_DB`,
  `SECURITY_PEPPER` y `PAGINATION_CURSOR_SECRET` estén definidos y válidos.
  Si falta alguno, la validación de `Settings` lanza un error y el proceso
  no arranca.

### `faker`

Usa **adaptadores en memoria** con datos sintéticos generados por la librería
`Faker`. La aplicación:

- **No** abre ninguna conexión a base de datos. El *lifespan* imprime un
  aviso y termina sin inicializar el motor.
- Inyecta `FakerUnitOfWork` (almacén en memoria compartido entre peticiones
  del mismo proceso) a los casos de uso.
- Precarga 25 entidades sintéticas por módulo al arrancar.
- `PG_*`, `SECURITY_PEPPER` y `PAGINATION_CURSOR_SECRET` **son opcionales**:
  si no se definen, se usan secretos efímeros generados al arrancar.

> **Advertencia**: los datos viven solo en la memoria del proceso y se
> pierden al reiniciarlo. **No usar en producción**. Pensado para
> desarrollo local, demos y pruebas sin infraestructura.

### Ejemplo

```env
REPOSITORY_DATA_SOURCE=database
```

```env
REPOSITORY_DATA_SOURCE=faker
```

---

## Configuración base

### APP_NAME

**Tipo**: string
**Por defecto**: `Microservicio con GenCLI`
**Obligatoria**: recomendada

Nombre del servicio. Se muestra en:

- El título de la documentación Swagger / ReDoc.
- El log de arranque (`Iniciando <APP_NAME> en modo <ENVIRONMENT>...`).
- El campo `title` del documento OpenAPI.

En producción, usar el nombre real del microservicio (p. ej.
`ms-catalog-service`).

### ENVIRONMENT

**Tipo**: string (libre, pero se recomienda uno de: `development`,
`production`, `staging`, `testing`)
**Por defecto**: `development`
**Obligatoria**: sí

Identifica el entorno de ejecución. Lo devuelve el endpoint `GET /health` en
el campo `environment`. Útil para que los balanceadores y los dashboards de
monitorización confirmen qué entorno están alcanzando.

No cambia el comportamiento interno de la aplicación por sí solo: es
informativo. Sin embargo, en combinación con `DEBUG=true` puede exponer
trazas detalladas.

### DEBUG

**Tipo**: booleano — `true` | `false`
**Por defecto**: `false`
**Obligatoria**: no

Controla el modo *debug* de FastAPI:

- `true`: FastAPI muestra el stacktrace completo ante errores no manejados y
  recarga los *routers* en caliente si se usa `--reload`. Útil en desarrollo.
- `false`: FastAPI oculta los detalles internos del error y solo devuelve el
  `problem+json` (RFC 9457) correspondiente.

> **Producción**: siempre `false`. Exponer stacktraces es un riesgo de
> fuga de información (revela rutas de archivos, versiones de librerías y
> lógica interna).

### API_VERSION

**Tipo**: string (formato semver recomendado: `MAJOR.MINOR.PATCH`)
**Por defecto**: `1.0.0`
**Obligatoria**: no

Versión semántica de la API. Se expone en el campo `version` del documento
OpenAPI y en la documentación Swagger. No afecta el enrutado (las rutas
cuelgan de `/api/v1` de forma fija).

### API_DESCRIPTION

**Tipo**: string (texto libre)
**Por defecto**: `API REST para modulos del microservicio`
**Obligatoria**: no

Descripción larga de la API. Se muestra en la cabecera de la documentación
Swagger / ReDoc. Útil para añadir contexto del negocio, contacto o enlaces a
repositorios.

---

## Documentación OpenAPI

Estas tres variables controlan las URLs donde FastAPI sirve la documentación
interactiva. En producción se recomienda **deshabilitarlas** para evitar
exponer el contrato de la API a terceros.

### OPENAPI_URL

**Tipo**: string (ruta URL) | `None` para deshabilitar
**Por defecto**: `/openapi.json`
**Obligatoria**: no

Ruta donde se sirve el JSON del esquema OpenAPI. Si se define como cadena
vacía o `None`, FastAPI no publica el esquema y `DOCS_URL` / `REDOC_URL` dejan
de funcionar.

> **Producción**: `OPENAPI_URL=` (vacío) para ocultar el esquema, o
> `/openapi.json` si se quiere exponer tras un API Gateway.

### DOCS_URL

**Tipo**: string (ruta URL) | `None` para deshabilitar
**Por defecto**: `/docs`
**Obligatoria**: no

Ruta donde se sirve la documentación Swagger UI. Si se define como cadena
vacía o `None`, Swagger no se publica.

> **Producción**: `DOCS_URL=` (vacío) para deshabilitar.

### REDOC_URL

**Tipo**: string (ruta URL) | `None` para deshabilitar
**Por defecto**: `/redoc`
**Obligatoria**: no

Ruta donde se sirve la documentación ReDoc (alternativa a Swagger con mejor
legibilidad). Si se define como cadena vacía o `None`, ReDoc no se publica.

> **Producción**: `REDOC_URL=` (vacío) para deshabilitar.

---

## PostgreSQL

Variables de conexión a la base de datos principal. **Solo son obligatorias
cuando `REPOSITORY_DATA_SOURCE=database`**. En modo `faker` se ignoran
completamente.

### PG_USER

**Tipo**: string
**Por defecto**: `None`
**Obligatoria**: sí, si `REPOSITORY_DATA_SOURCE=database`

Usuario de la base de datos. Se inyecta en el DSN de conexión
(`postgresql+asyncpg://<user>:<password>@<host>:<port>/<db>`).

> **Producción**: usar un usuario con privilegios mínimos (`SELECT`,
> `INSERT`, `UPDATE`, `DELETE` sobre las tablas del esquema; `CREATE` y
> `INDEX` solo si se ejecutan las migraciones desde el mismo servicio, lo
> cual **no se recomienda** — las migraciones deben correrlas un Job
> separado con un usuario privilegiado.

### PG_PASSWORD

**Tipo**: string (secreto)
**Por defecto**: `None`
**Obligatoria**: sí, si `REPOSITORY_DATA_SOURCE=database`

Contraseña del usuario `PG_USER`. Se inyecta en el DSN sin escapar; si
contiene caracteres especiales (`@`, `:`, `/`, `#`), la construcción del DSN
puede romper. En ese caso, considera usar un usuario sin caracteres
especiales en la contraseña, o refactorizar `config.py` para usar
`sqlalchemy.URL.create()` con escapado automático.

> **Seguridad**: nunca hardcodear en la imagen. Inyectar desde un gestor de
> secretos (AWS Secrets Manager, HashiCorp Vault, Kubernetes Secrets).

### PG_HOST

**Tipo**: string (hostname o IP)
**Por defecto**: `None`
**Obligatoria**: sí, si `REPOSITORY_DATA_SOURCE=database`

Host donde escucha PostgreSQL. Puede ser:

- `localhost` para desarrollo local.
- Un nombre DNS interno (p. ej. `db.internal.svc.cluster.local`) en
  Kubernetes.
- Una IP privada (p. ej. `10.0.1.42`).

### PG_PORT

**Tipo**: entero
**Por defecto**: `5432`
**Obligatoria**: no

Puerto TCP donde escucha PostgreSQL. El estándar es `5432`; solo cambia si
se expone PostgreSQL en otro puerto.

### PG_DB

**Tipo**: string
**Por defecto**: `None`
**Obligatoria**: sí, si `REPOSITORY_DATA_SOURCE=database`

Nombre de la base de datos (esquema) a la que conectarse. Debe existir
antes de arrancar el servicio; la aplicación no la crea.

### PG_SSLMODE

**Tipo**: enumerado — `disable` | `require`
**Por defecto**: `disable`
**Obligatoria**: no

Controla el cifrado TLS/SSL de la conexión a PostgreSQL:

- `disable`: la conexión viaja en texto plano. Solo aceptable dentro de una
  red aislada (VPC, cluster interno) donde el tráfico no sale del perímetro.
  El driver (`asyncpg`) intenta SSL por defecto, por lo que la aplicación lo
  deshabilita explícitamente con `ssl=False` para evitar timeouts en
  entornos sin soporte TLS.
- `require`: la conexión exige TLS con un certificado válido. La aplicación
  construye un contexto SSL estándar con `ssl.create_default_context()` y lo
  pasa al driver.

> **Producción**: `require` siempre que PostgreSQL esté en otra red, en la
> nube o cuando el tráfico cruce segmentos no aislados.

### PG_CONNECT_TIMEOUT

**Tipo**: entero (segundos)
**Por defecto**: `10`
**Obligatoria**: no

Tiempo máximo que `asyncpg` espera para establecer la conexión TCP antes de
considerarla fallida. Se pasa como `{"timeout": <valor>}` en los argumentos
de conexión.

> **Producción**: mantener `10` o subir a `15` si la red tiene latencia
> alta. Valores muy bajos (1-3) causan fallos espurios; valores muy altos
> (60+) retrasan el arranque sin beneficio real.

### DSN generado

La aplicación construye el DSN internamente con el formato:

```
postgresql+asyncpg://<PG_USER>:<PG_PASSWORD>@<PG_HOST>:<PG_PORT>/<PG_DB>?ssl=disable
```

(o sin `?ssl=disable` si `PG_SSLMODE=require`).

No hay una variable `DATABASE_URL` separada; el DSN siempre se compone desde
las variables individuales.

---

## SQL Server

Variables para una integración opcional con SQL Server (no usadas por los
módulos generados por GenCLI; pensadas para integraciones externas que
consulten bases heredadas). **No son obligatorias** salvo que el código de
integración las consuma.

### MS_USER

**Tipo**: string | `None`
**Por defecto**: `None`
**Obligatoria**: solo si se usa SQL Server

Usuario de SQL Server.

### MS_PASSWORD

**Tipo**: string (secreto) | `None`
**Por defecto**: `None`
**Obligatoria**: solo si se usa SQL Server

Contraseña del usuario `MS_USER`.

### MS_HOST

**Tipo**: string | `None`
**Por defecto**: `None`
**Obligatoria**: solo si se usa SQL Server

Host o IP de la instancia SQL Server.

### MS_PORT

**Tipo**: entero
**Por defecto**: `1433`
**Obligatoria**: no

Puerto TCP de SQL Server (estándar: `1433`).

### MS_DB

**Tipo**: string | `None`
**Por defecto**: `None`
**Obligatoria**: solo si se usa SQL Server

Nombre de la base de datos SQL Server a la que conectarse.

### DSN generado

Si se invoca `settings.ms_dsn`, la aplicación construye:

```
mssql+aioodbc://<MS_USER>:<MS_PASSWORD>@<MS_HOST>:<MS_PORT>/<MS_DB>?driver=ODBC+Driver+18+for+SQL+Server
```

Requiere el driver ODBC 18 instalado en el contenedor. Si falta, la
conexión falla al arrancar.

---

## Mensajería y caché

### RABBITMQ_URL

**Tipo**: string (URL AMQP)
**Por defecto**: `amqp://guest:guest@localhost:5672/`
**Obligatoria**: solo si se usa mensajería

URL de conexión a RabbitMQ (bróker de mensajería AMQP). Formato:

```
amqp://<usuario>:<password>@<host>:<puerto>/<vhost>
```

- El `<vhost>` por defecto es `/` (vacío tras el último `:`).
- En producción, usar credenciales dedicadas y un vhost aislado por
  servicio (p. ej. `amqp://svc-catalog:s3cr3t@rabbitmq.internal:5672/catalog`).

> **Nota**: el microservicio base no publica ni consume colas por defecto.
  Esta variable está pensada para módulos futuros que publiquen eventos de
  dominio (p. ej. `UserCreated`, `ProductDeleted`) hacia un *event bus*.

### REDIS_URL

**Tipo**: string (URL Redis)
**Por defecto**: `redis://localhost:6379/0`
**Obligatoria**: solo si se usa caché

URL de conexión a Redis. Formato:

```
redis://[:<password>@]<host>:<puerto>/<db>
```

- `<db>` es un número entero (0-15) que selecciona la base lógica de Redis.
- En producción, usar una instancia dedicada y proteger con contraseña.

> **Nota**: al igual que `RABBITMQ_URL`, el microservicio base no usa Redis
  directamente. Está disponible para módulos que necesiten caché de lectura,
  rate-limiting o sesiones distribuidas.

---

## Seguridad (API Keys)

### SECURITY_PEPPER

**Tipo**: string (secreto)
**Por defecto**: `""` (cadena vacía)
**Obligatoria**: sí, si `REPOSITORY_DATA_SOURCE=database`

Pepper (secreto de servidor) que se mezcla con el *secret* de cada API key
antes de hashear con HMAC-SHA256. Esto significa que aunque la base de datos
se filtre, las API keys **no pueden verificarse** sin conocer el pepper.

**Restricciones**:

- Debe tener **al menos 32 caracteres**. Si tiene menos, la validación de
  `Settings` aborta el arranque.
- En modo `database`, si está vacío o tiene menos de 32 caracteres, el
  proceso no arranca.
- En modo `faker`, si está vacío se permite un pepper efímero generado al
  arrancar (suficiente para desarrollo).

**Generación**:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Esto produce una cadena aleatoria de ~63 caracteres con entropía
criptográfica suficiente.

> **Producción**: generar una vez y rotar periódicamente. La rotación
> invalida todas las API keys existentes (deben regenerarse). Inyectar
> desde el gestor de secretos. **Nunca** subir al repositorio ni a la
> imagen Docker.

---

## Paginación keyset

### PAGINATION_CURSOR_SECRET

**Tipo**: string (secreto) | `None`
**Por defecto**: `None`
**Obligatoria**: sí, si `REPOSITORY_DATA_SOURCE=database` y se usan los
endpoints paginados (`/paginated` o `/find-by` con `pagination: true`)

Secreto usado para firmar los cursores de paginación keyset con
HMAC-SHA256. Los cursores son tokens opacos que el cliente recibe y
devuelve tal cual; si un cliente los altera, la firma no coincide y se
rechazan con HTTP 400 (`InvalidCursorError`).

**Restricciones**:

- Si se define, debe tener **al menos 32 caracteres**. La validación de
  `Settings` rechaza cadenas más cortas.
- Si **no se define** (ausente del `.env` y del SO):
  - En modo `database`: la primera petición a un endpoint paginado lanza
    `RuntimeError("Define PAGINATION_CURSOR_SECRET para usar paginación
    keyset.")` y la API devuelve 500.
  - En modo `faker`: se genera un secreto efímero con
    `secrets.token_urlsafe(48)` al arrancar. Suficiente para desarrollo;
    no persiste entre reinicios.
- **Importante**: si se define como cadena vacía (`PAGINATION_CURSOR_SECRET=`)
  en el `.env`, `pydantic-settings` lo lee como `""` (string de 0
  caracteres), no como `None`. La validación `min_length=32` lo rechaza y el
  proceso no arranca. En modo `faker` simplemente **omita la variable** del
  `.env` para obtener el secreto efímero.

**Generación**:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> **Producción**: usar un secreto distinto al de `SECURITY_PEPPER`. La
> rotación invalida los cursores en vuelo (los clientes deben pedir la
> primera página de nuevo). Inyectar desde el gestor de secretos.

---

## Búsqueda (Meilisearch)

### MEILISEARCH_URL

**Tipo**: string (URL HTTP/HTTPS)
**Por defecto**: `http://localhost:7700`
**Obligatoria**: solo si se usa Meilisearch

URL de la instancia de Meilisearch (motor de búsqueda full-text). En
producción, usar HTTPS con un certificado válido.

### MEILISEARCH_MASTER_KEY

**Tipo**: string (secreto) | `None`
**Por defecto**: `None`
**Obligatoria**: solo si la instancia Meilisearch exige autenticación

Clave maestra de Meilisearch. Si la instancia está protegida (recomendado en
producción), esta clave se usa para autenticar las peticiones de indexación
y búsqueda.

> **Seguridad**: la clave maestra tiene acceso total. En producción,
> considerar crear claves de API con permisos limitados (búsqueda vs.
> escritura) y ajustar el código para usarlas. Nunca subir al repositorio.

---

## Matriz de obligatoriedad por modo

### Modo `database` (producción)

| Variable | Obligatoria | Notas |
|---|---|---|
| `REPOSITORY_DATA_SOURCE` | sí | `database` |
| `PG_USER` | sí | |
| `PG_PASSWORD` | sí | Secreto |
| `PG_HOST` | sí | |
| `PG_PORT` | no | Default `5432` |
| `PG_DB` | sí | |
| `PG_SSLMODE` | recomendada | `require` en producción |
| `PG_CONNECT_TIMEOUT` | no | Default `10` |
| `SECURITY_PEPPER` | sí | Mín. 32 caracteres; secreto |
| `PAGINATION_CURSOR_SECRET` | sí | Mín. 32 caracteres; secreto |
| `APP_NAME` | recomendada | |
| `ENVIRONMENT` | sí | `production` |
| `DEBUG` | recomendada | `false` |
| `OPENAPI_URL` | recomendada | `""` para ocultar |
| `DOCS_URL` | recomendada | `""` para ocultar |
| `REDOC_URL` | recomendada | `""` para ocultar |

### Modo `faker` (desarrollo / demo)

| Variable | Obligatoria | Notas |
|---|---|---|
| `REPOSITORY_DATA_SOURCE` | sí | `faker` |
| `PG_*` | no | Se ignoran |
| `SECURITY_PEPPER` | no | Se usa efímero |
| `PAGINATION_CURSOR_SECRET` | no | Se usa efímero; **omitir** la variable (no dejarla vacía) |
| `APP_NAME` | recomendada | |
| `ENVIRONMENT` | recomendada | `development` |
| `DEBUG` | recomendada | `true` |

---

## Ejemplo de `.env` para producción

```env
# Origen de datos
REPOSITORY_DATA_SOURCE=database

# Configuración base
APP_NAME=ms-catalog-service
ENVIRONMENT=production
DEBUG=false
API_VERSION=1.0.0
API_DESCRIPTION=Microservicio de catálogo de productos

# Documentación OpenAPI (oculta en producción)
OPENAPI_URL=
DOCS_URL=
REDOC_URL=

# PostgreSQL
PG_USER=svc_catalog_app
PG_PASSWORD=<inyectado-por-secret-manager>
PG_HOST=db.internal.svc.cluster.local
PG_PORT=5432
PG_DB=catalog
PG_SSLMODE=require
PG_CONNECT_TIMEOUT=10

# Seguridad
SECURITY_PEPPER=<inyectado-por-secret-manager>
PAGINATION_CURSOR_SECRET=<inyectado-por-secret-manager>

# Infraestructura (si aplica)
RABBITMQ_URL=amqp://svc_catalog:<password>@rabbitmq.internal:5672/catalog
REDIS_URL=redis://:<password>@redis.internal:6379/0

# Búsqueda (si aplica)
MEILISEARCH_URL=https://search.internal
MEILISEARCH_MASTER_KEY=<inyectado-por-secret-manager>
```

## Ejemplo de `.env` para desarrollo (modo faker)

```env
REPOSITORY_DATA_SOURCE=faker
APP_NAME=Microservicio con GenCLI
ENVIRONMENT=development
DEBUG=true
API_VERSION=1.0.0
```

No se necesitan más variables: los secretos y las credenciales de DB se
ignoran o se generan efímeramente.

---

## Checklist de despliegue para DevOps

1. **Definir `REPOSITORY_DATA_SOURCE`** según el entorno.
2. Si es `database`:
   - [ ] Crear la base de datos `PG_DB` en PostgreSQL antes de arrancar.
   - [ ] Crear el usuario `PG_USER` con privilegios mínimos.
   - [ ] Configurar `PG_SSLMODE=require` si el tráfico cruza redes no
         aisladas.
   - [ ] Ejecutar las migraciones de tabla e índice desde un Job separado
         (`poe create_<modulo>_table`, `poe create_<modulo>_index`).
3. Generar e inyectar los dos secretos:
   - [ ] `SECURITY_PEPPER` (≥ 32 caracteres).
   - [ ] `PAGINATION_CURSOR_SECRET` (≥ 32 caracteres, distinto del pepper).
4. Endurecer la exposición HTTP:
   - [ ] `DEBUG=false`.
   - [ ] `OPENAPI_URL`, `DOCS_URL`, `REDOC_URL` vacíos si no se quiere
         exponer documentación.
5. Si se usan mensajería / caché / búsqueda:
   - [ ] Configurar `RABBITMQ_URL`, `REDIS_URL`, `MEILISEARCH_URL` con
         credenciales dedicadas.
6. Verificar el health check tras el despliegue:
   ```bash
   curl https://<host>/health
   # -> {"status":"ok","environment":"production"}
   ```