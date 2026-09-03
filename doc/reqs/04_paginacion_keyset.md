# Paginación Keyset

`--uc-list-paginated` ordena las entidades activas de forma ascendente por
`(created_at, id_<entidad>)`. La consulta recibe un cursor firmado y añade una
condición keyset, por lo que no usa `OFFSET` ni ejecuta `COUNT(*)`.

La migración de cada tabla generada debe incluir este índice parcial:

```sql
CREATE INDEX ix_<entidades>_active_created_id
ON <entidades> (created_at, id_<entidad>)
WHERE deleted_at IS NULL;
```

El endpoint pide `limit + 1` filas. La fila adicional solo determina
`has_next`; no se devuelve. El cursor siguiente contiene la posición de la
última fila visible y está protegido con HMAC-SHA256 mediante
`PAGINATION_CURSOR_SECRET` (mínimo 32 caracteres).

Antes de exponer cualquier endpoint paginado se debe definir:

```env
PAGINATION_CURSOR_SECRET=<secreto-aleatorio-de-al-menos-32-caracteres>
```

## Find-by

`--uc-find-by` expone `POST /<entidades>/find-by`. El cuerpo contiene `field` y
`query` (`operator`: `equals`, `contains` o `starts_with`; `value`). El mapa de
campos y tipos se genera exclusivamente desde las propiedades de la entidad.
`contains` y `starts_with` solo aceptan campos `str`.

`pagination` es opcional y por defecto es `false`: la respuesta está limitada y
no emite cursor. Con `pagination: true`, `limit` y `cursor` se transportan en el
cuerpo y reutilizan el cursor HMAC y el orden `(created_at, id_<entidad>)`.
El adaptador selecciona columnas y operadores de mapas estáticos y SQLAlchemy
parametriza los valores; no se construye SQL a partir del payload.
