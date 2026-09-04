# Guía de comandos GenCLI

GenCLI genera y hace crecer módulos hexagonales de forma incremental e idempotente.
Requisitos: binario `./gen` en la raíz del proyecto, `gen_config.json` (ignorado por
git; copia de `gen_config.example.json`) apuntando `templates_root` a
`.gen_cli/templates` de este repositorio, y `arq.json` en la raíz.

## Módulo base

```bash
./gen --hex User "nombre:str,email:str"
```

Genera el núcleo de `src/modules/users/`: entidad, puerto de repositorio, excepciones,
modelo SQLAlchemy, adaptador vacío, composition root, router y schemas con marcadores.
**No** crea endpoints ni registra el router en `main.py`.

## Casos de uso (en cualquier orden, sobre un módulo existente)

```bash
./gen --uc-list            User "nombre:str,email:str"   # GET  /api/v1/users/
./gen --uc-list-paginated  User "nombre:str,email:str"   # GET  /api/v1/users/paginated
./gen --uc-find-by         User "nombre:str,email:str"   # POST /api/v1/users/find-by
./gen --uc-create          User "nombre:str,email:str"   # POST /api/v1/users/
./gen --uc-get             User "nombre:str,email:str"   # GET  /api/v1/users/{identifier}
./gen --uc-update          User "nombre:str,email:str"   # PUT  /api/v1/users/{identifier}
./gen --uc-delete          User "nombre:str,email:str"   # DELETE /api/v1/users/{identifier}
```

Cada comando genera caso de uso, controller, schemas, ruta, prueba unitaria con fake
repository (sin Postgres) y completa puerto/adaptador/providers/router/main.py
mediante hooks idempotentes. Repetir un comando no duplica nada; ejecutarlo contra un
módulo inexistente falla sin modificar archivos.

Propiedades soportadas: `str`, `int`, `float`, `bool`, `datetime`, `UUID`.

## Soft delete y filtrado condicional de `deleted_at`

El comando `--uc-delete` implementa **soft delete** (borrado lógico): en
lugar de eliminar la fila, fija `deleted_at` con la marca temporal UTC del
momento del borrado. Las lecturas posteriores excluyen automáticamente las
filas con `deleted_at` no nulo.

### Columna `deleted_at`

La columna `deleted_at` se genera **siempre** en `--hex` (entidad, modelo
SQLAlchemy y migración `create_table`). Es `nullable=True` y por defecto
`NULL` (activo). El índice parcial keyset también la usa:

```sql
CREATE INDEX ix_<ent>s_active_created_id
ON <ent>s (created_at, id_<ent>)
WHERE deleted_at IS NULL;
```

### Filtro condicional en los casos de uso de lectura

Los hooks de `--uc-list`, `--uc-list-paginated`, `--uc-find-by`, `--uc-get`
y `--uc-update` detectan si el modelo SQLAlchemy del módulo define la
columna `deleted_at` antes de generar el filtro `deleted_at IS NULL` en la
query. Esto se hace en tiempo de **generación de código** (no en runtime):
el hook lee `models.py` y, si encuentra `deleted_at`, incluye el filtro;
si no lo encuentra, genera la query sin el filtro.

| Caso de uso | Filtro generado si `deleted_at` existe |
|---|---|
| `--uc-list` | `.where(Model.deleted_at.is_(None))` |
| `--uc-list-paginated` | `select(Model).where(Model.deleted_at.is_(None))` |
| `--uc-find-by` | `.where(Model.deleted_at.is_(None), predicate)` |
| `--uc-get` | `.where(Model.id == identifier, Model.deleted_at.is_(None))` |
| `--uc-update` | `.where(Model.id == identifier, Model.deleted_at.is_(None))` |

Si `deleted_at` no existe en el modelo, el filtro se omite y la query
funciona sin error. Esto permite que módulos sin `--uc-delete` (o donde se
eliminó con `delete_use_case`) no rompan al consultar la tabla.

### Migración `ALTER TABLE` para módulos existentes

Si la tabla ya existe **sin** la columna `deleted_at` (por ejemplo, un
módulo creado antes de este cambio), `--uc-delete` genera un script de
migración opcional para añadirla:

```bash
uv run poe add_soft_delete_<module>s
```

El script ejecuta:

```sql
ALTER TABLE <tabla> ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS ix_<tabla>_active_created_id
ON <tabla> (created_at, id_<ent>) WHERE deleted_at IS NULL;
```

La migración es **opcional**: el usuario decide cuándo ejecutarla. Requiere
`REPOSITORY_DATA_SOURCE=database` y credenciales `PG_*` en `.env`.

### Eliminar `--uc-delete` con `delete_use_case`

Al ejecutar `poe delete_use_case <Module> delete`, el script elimina el
método `soft_delete` del puerto, adaptador y faker, la ruta HTTP, el
controller, el test y el provider. **No elimina la columna `deleted_at`**
de la entidad ni del modelo: la columna es inofensiva (nullable, NULL por
defecto) y evita reescribir las queries de los demás casos de uso que ya
filtran por ella.

Si se vuelve a ejecutar `./gen --uc-delete`, el hook detecta que `deleted_at`
ya existe y no la duplica.

## Ejemplo completo (módulo de referencia)

```bash
./gen --hex Product "name:str,price:float,is_physical:bool"
./gen --uc-create Product "name:str,price:float,is_physical:bool"
./gen --uc-get Product "name:str,price:float,is_physical:bool"
./gen --uc-list Product "name:str,price:float,is_physical:bool"
./gen --uc-list-paginated Product "name:str,price:float,is_physical:bool"
./gen --uc-find-by Product "name:str,price:float,is_physical:bool"
./gen --uc-update Product "name:str,price:float,is_physical:bool"
./gen --uc-delete Product "name:str,price:float,is_physical:bool"
```

## Consultas SQL custom (`gen_custom_query`)

Genera un endpoint vertical completo que ejecuta una consulta SQL nativa de
PostgreSQL de forma segura con parámetros tipados. Pensado para consumir
vistas, stored procedures, joins, agregaciones (`SUM`, `AVG`, `COUNT`) u
otras consultas que no encajan en el patrón CRUD del generador.

A diferencia de `./gen --uc-*`, este comando es un script Python (no pasa
por el binario `./gen`) porque el SQL puede ser multilínea y contener
caracteres especiales.

### Sintaxis

```bash
poe gen_custom_query <Module> --route <route> --method <GET|POST|PUT|DELETE> \
    --sql "<sql>" [--params "name:type,..."] [--dry-run]

poe gen_custom_query <Module> --route <route> --method <GET|POST|PUT|DELETE> \
    --sql-file <path.sql> [--params "name:type,..."] [--dry-run]
```

### Parámetros

| Argumento | Descripción |
|---|---|
| `<Module>` | Módulo destino: `Product`, `product` o `products` |
| `--route` | Nombre de la ruta HTTP (ej: `sales-by-region`, `inventory-summary`) |
| `--method` | Método HTTP: `GET`, `POST`, `PUT` o `DELETE` |
| `--sql` | Consulta SQL inline (PostgreSQL nativo) |
| `--sql-file` | Ruta a archivo `.sql` con la consulta (alternativa a `--sql`) |
| `--params` | Parámetros tipados: `"region:str,month:int"` (opcional) |
| `--dry-run` | Preview sin modificar nada |

### Tipos de parámetros soportados

`str`, `int`, `float`, `bool`, `datetime`, `UUID`

### Archivos generados

| Archivo | Descripción |
|---|---|
| `use_cases/custom_<route>.py` | Caso de uso que orquesta la consulta |
| `infrastructure/http/controllers/custom_<route>_controller.py` | Controller HTTP |
| `infrastructure/persistence/custom_repositories.py` | Repositorio custom con `text()` (se crea o extiende) |
| `tests/unit/modules/<mod>/test_custom_<route>.py` | Test unitario con fake repository |

Además inyecta en `dependencies.py`, `schemas.py` y `routers.py` (igual que
los `--uc-*` estándar).

### Seguridad anti-inyección SQL

Los parámetros de runtime **siempre** van parameterized con `text()` y un
dict de valores:

```python
# SEGURO: SQLAlchemy envía :name como $1 al driver asyncpg
result = await self._session.execute(
    text("WHERE r.name = :name"),
    {"name": name},
)
```

El driver parametriza el valor: nunca se interpola en el SQL. El script
**nunca** genera `f"... WHERE r.name = '{name}'"` (inyección).

La consulta SQL embebida es confianza de desarrollador (no de usuario): se
escribe en el código fuente en tiempo de generación, igual que cualquier SQL
escrito a mano. El riesgo de inyección está en los **parámetros de runtime**,
no en la query estática.

El script valida que todo `:param` en el SQL esté declarado en `--params`. Si
falta alguno, aborta sin modificar nada.

### Ejemplos

#### Consulta sin parámetros (vista o agregación simple)

```bash
poe gen_custom_query Product \
  --route inventory-summary \
  --method GET \
  --sql "SELECT category, COUNT(*) AS total FROM products GROUP BY category"
```

Genera `GET /api/v1/products/inventory-summary` que devuelve:

```json
{"rows": [{"category": "electronics", "total": 42}, ...]}
```

#### Consulta con parámetros (join + WHERE dinámico)

```bash
poe gen_custom_query Product \
  --route sales-by-name \
  --method POST \
  --sql "SELECT name, SUM(price) AS total FROM products WHERE name = :name GROUP BY name" \
  --params "name:str"
```

Genera `POST /api/v1/products/sales-by-name` que acepta:

```json
{"name": "laptop"}
```

Y devuelve:

```json
{"rows": [{"name": "laptop", "total": 9999.99}]}
```

#### Consulta con SQL desde archivo

```bash
poe gen_custom_query Product \
  --route monthly-report \
  --method POST \
  --sql-file queries/monthly_report.sql \
  --params "month:int,year:int"
```

#### Stored procedure

```bash
poe gen_custom_query Product \
  --route calculate-stock \
  --method POST \
  --sql "CALL calculate_stock(:warehouse_id)" \
  --params "warehouse_id:UUID"
```

### Response

El endpoint devuelve `{"rows": [...]}` donde cada elemento es un diccionario
con todos los campos que trae la consulta. Los tipos son `object` (sin tipar)
porque el resultado depende del SQL en runtime. El desarrollador puede
tipar el response manualmente editando `schemas.py` si lo desea.

### Eliminar una consulta custom

```bash
poe delete_use_case Product custom-inventory-summary
poe delete_use_case Product custom-sales-by-name
```

El formato es `custom-<route>` (con guiones, igual que se pasó a `--route`).
El script elimina el use case, controller, test, schemas, provider, ruta y
el método del repositorio custom. Si el `custom_repositories.py` queda sin
métodos, se borra el archivo completo.

## Ejemplos de uso de la API generada

```bash
# Listado acotado
curl http://localhost:8000/api/v1/users/?limit=10

# Paginación keyset: usar next_cursor de la respuesta anterior como cursor
curl "http://localhost:8000/api/v1/users/paginated?limit=50&cursor=<next_cursor>"

# Búsqueda dinámica (sin paginar, respuesta limitada por el servidor)
curl -X POST http://localhost:8000/api/v1/users/find-by \
  -H "Content-Type: application/json" \
  -d '{"field": "email", "query": {"operator": "contains", "value": "@acme"}}'

# Búsqueda dinámica paginada
curl -X POST http://localhost:8000/api/v1/users/find-by \
  -H "Content-Type: application/json" \
  -d '{"field": "nombre", "query": {"operator": "starts_with", "value": "A"},
       "pagination": true, "limit": 50}'
```

## Eliminar un módulo

```bash
poe delete_module User          # también acepta: user, users
poe delete_module User --dry-run  # preview sin modificar nada
```

Elimina `src/modules/users/`, sus pruebas en `tests/unit/modules/users/`
(y `tests/e2e/users/` si existe) y remueve de `src/main.py` el import y el
`include_router` del módulo. Acepta `User`, `user` o `users`.

Orden de operaciones (fallo seguro): primero limpia `main.py` con escritura
atómica y validación `ast`; solo entonces borra los directorios. Si el módulo
no existe, falla sin modificar nada. Otros módulos registrados quedan intactos.

## Eliminar un caso de uso

```bash
poe delete_use_case <Module> <use-case> [--dry-run]
```

Elimina **un solo caso de uso** del módulo y limpia todas sus huellas en los
archivos compartidos, sin afectar los demás casos de uso. Es la operación
inversa a `./gen --uc-*`.

### Sintaxis

```bash
poe delete_use_case Product list                 # elimina --uc-list
poe delete_use_case Product list --dry-run       # preview sin modificar nada
poe delete_use_case Product list-paginated
poe delete_use_case Product find-by
poe delete_use_case Product create
poe delete_use_case Product get
poe delete_use_case Product update
poe delete_use_case Product delete
poe delete_use_case Product custom-inventory-summary  # elimina gen_custom_query
```

El nombre del módulo acepta `Product`, `product` o `products` (igual que
`delete_module`). El nombre del caso de uso acepta las formas cortas
(`list`, `create`, `get`, …) o las largas con prefijo (`--uc-list`,
`--uc-create`, …). Para consultas custom, usar `custom-<route>` (ej:
`custom-inventory-summary`).

### Casos de uso soportados

| Argumento | Equivalente GenCLI | Ruta HTTP eliminada |
|---|---|---|
| `list` | `--uc-list` | `GET /api/v1/<ent>s/` |
| `list-paginated` | `--uc-list-paginated` | `GET /api/v1/<ent>s/paginated` |
| `find-by` | `--uc-find-by` | `POST /api/v1/<ent>s/find-by` |
| `create` | `--uc-create` | `POST /api/v1/<ent>s/` |
| `get` | `--uc-get` | `GET /api/v1/<ent>s/{identifier}` |
| `update` | `--uc-update` | `PUT /api/v1/<ent>s/{identifier}` |
| `delete` | `--uc-delete` | `DELETE /api/v1/<ent>s/{identifier}` |
| `custom-<route>` | `gen_custom_query --route <route>` | `<method> /api/v1/<ent>s/<route>` |

### Qué elimina

Por cada caso de uso, el script limpia **9 puntos** del módulo:

| Archivo | Acción |
|---|---|
| `use_cases/<uc>_<ent>s.py` | Borra el archivo |
| `infrastructure/http/controllers/<uc>_<ent>s_controller.py` | Borra el archivo |
| `tests/unit/modules/<ent>s/test_<uc>_<ent>s.py` | Borra el archivo |
| `domain/repositories.py` | Elimina el método del puerto |
| `infrastructure/persistence/repositories.py` | Elimina el método del adaptador + imports huérfanos |
| `infrastructure/persistence/faker_repositories.py` | Elimina el método del faker + imports huérfanos |
| `infrastructure/http/dependencies.py` | Elimina el import del UC y la función `get_<uc>_<ent>s` |
| `infrastructure/http/schemas.py` | Elimina las clases de schema y las funciones mapper |
| `infrastructure/http/routers.py` | Elimina el import del controller/UC/provider/schema y el decorador + ruta |

`src/main.py` **no se modifica**: el router del módulo sigue registrado
porque los demás casos de uso siguen activos. La limpieza de `main.py` la
hace `delete_module` cuando se elimina el módulo completo.

Al eliminar `delete` (`poe delete_use_case <Module> delete`), la columna
`deleted_at` **permanece** en la entidad y el modelo. Ver la sección
[Soft delete y filtrado condicional](#soft-delete-y-filtrado-condicional-de-deleted_at)
para más detalle.

### Garantías de seguridad

- **Escritura atómica**: todos los archivos compartidos se validan con
  `ast.parse` antes de persistir. Si el código resultante no compila, no se
  escribe nada y el proceso aborta con error.
- **Idempotente**: si el caso de uso ya no existe (falta el archivo del use
  case), el script reporta que no hay cambios y no modifica nada.
- **Fallo seguro**: si un archivo compartido no existe o falta un marcador
  `gencli:*`, el script aborta sin modificar nada.
- **`--dry-run`**: muestra todas las acciones que ejecutaría sin tocar los
  archivos.

### Ejemplo completo

Eliminar `list` y `delete` de un módulo `Product` con los 7 casos de uso:

```bash
poe delete_use_case Product list
poe delete_use_case Product delete
```

Tras la ejecución, `src/modules/products/` conserva 5 casos de uso
(`create`, `get`, `list-paginated`, `find-by`, `update`) con sus rutas,
schemas, providers y métodos de repositorio intactos. Las rutas
`GET /api/v1/products/` y `DELETE /api/v1/products/{identifier}` desaparecen
del router.

## Variable de entorno obligatoria para paginación

Los endpoints con cursor firman el token con HMAC-SHA256 y requieren en `.env`:

```env
PAGINATION_CURSOR_SECRET=<secreto-aleatorio-de-al-menos-32-caracteres>
```

Sin ella, el provider del cursor falla al iniciar la petición. Los tests unitarios
generados usan un secreto propio y no dependen de esta variable. El índice parcial
que necesita cada tabla está documentado en
[reqs/04_paginacion_keyset.md](reqs/04_paginacion_keyset.md).
