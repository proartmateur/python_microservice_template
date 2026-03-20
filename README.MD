# Proyecto base para API REST y microservicios con Python

## Usar uv

instalar uv:
```bash
pip install uv
```

En caso de que no se pueda usar el comando uv directamente:

```bash
python -m uv
```

instalar dependencias

```bash
uv sync --all-extras
```

## Ejecutar el proyecto

Ejecutar en modo desarrollo

```bash
uv run poe dev
```

## Documentacion OpenAPI (Swagger)

Con la API ejecutandose en local, puedes abrir:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

Variables de entorno disponibles para personalizar la documentacion:

- `API_VERSION` (ej. `1.0.0`)
- `API_DESCRIPTION`
- `DOCS_URL` (ej. `/docs`)
- `REDOC_URL` (ej. `/redoc`)
- `OPENAPI_URL` (ej. `/openapi.json`)

Ejemplo de endpoint documentado:

- `POST /api/v1/users/` crea un usuario
- `GET /api/v1/users/` lista usuarios con paginado (`limit`, `page`)
- `GET /api/v1/users/{user_id}` consulta un usuario por UUID
- `DELETE /api/v1/users/{user_id}` aplica soft delete


Ejecutar en modo productivo

```bash
uv run poe start
```

## Ejecutar pruebas

```bash
uv run poe test
```

## Linting

```bash
uv run poe lint
```
## Formatear código

```bash
uv run poe format
```

## Chequear tipos

```bash
uv run poe typecheck
```

## Crear tabla `petras` si no existe

```bash
uv run poe init_petras_table
```

## Agregar columna `deleted_at` en `users` (soft delete)

Si ya tenias la tabla `users` creada antes del soft delete, ejecuta:

```bash
uv run poe add_users_deleted_at_column
```

