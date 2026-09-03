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
```

El nombre del módulo acepta `Product`, `product` o `products` (igual que
`delete_module`). El nombre del caso de uso acepta las formas cortas
(`list`, `create`, `get`, …) o las largas con prefijo (`--uc-list`,
`--uc-create`, …).

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
