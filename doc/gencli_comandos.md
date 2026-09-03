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

## Variable de entorno obligatoria para paginación

Los endpoints con cursor firman el token con HMAC-SHA256 y requieren en `.env`:

```env
PAGINATION_CURSOR_SECRET=<secreto-aleatorio-de-al-menos-32-caracteres>
```

Sin ella, el provider del cursor falla al iniciar la petición. Los tests unitarios
generados usan un secreto propio y no dependen de esta variable. El índice parcial
que necesita cada tabla está documentado en
[reqs/04_paginacion_keyset.md](reqs/04_paginacion_keyset.md).
