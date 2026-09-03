# Migraciones de base de datos

Las migraciones son **opcionales**: el usuario decide cuándo ejecutarlas.
Cada módulo generado con `--hex` incluye dos scripts de migración:

## Crear tabla + índice parcial

Crea la tabla (si no existe) y el índice parcial keyset para paginación
eficiente:

```sql
CREATE INDEX ix_<entidades>_active_created_id
ON <entidades> (created_at, id_<entidad>)
WHERE deleted_at IS NULL;
```

### Ejecutar

Ubica la tarea en `pyproject.toml` bajo `[tool.poe.tasks]`:

```toml
create_<snake_name>s_table = "python src/modules/<snake_name>s/scripts/create_<snake_name>s_table.py"
```

```bash
uv run poe create_<snake_name>s_table
```

Requiere `REPOSITORY_DATA_SOURCE=database` y credenciales `PG_*` en `.env`.

## Crear solo el índice parcial

Si la tabla ya existe pero falta el índice keyset:

```toml
create_<snake_name>s_index = "python src/modules/<snake_name>s/scripts/create_<snake_name>s_index.py"
```

```bash
uv run poe create_<snake_name>s_index
```

## Índice parcial keyset

El índice `ix_<entidades>_active_created_id` es fundamental para el rendimiento
de los endpoints `--uc-list-paginated` y `--uc-find-by` con `pagination: true`.
Sin este índice, la consulta keyset debe ordenar todas las filas activas en
memoria, lo que degrada en tablas grandes.

El índice es **parcial** (`WHERE deleted_at IS NULL`): solo indexa las filas
activas, reduciendo tamaño y manteniendo el orden `(created_at, id)`.