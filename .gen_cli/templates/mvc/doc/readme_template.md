# Cómo usar el módulo <ent>s

Para que las rutas de API funcionen es necesario agregar en main.py
el router del módulo.

1. Importar en los encabezados de main el router
```python
from src.modules.<snake_name>s.infrastructure.http.routers import router as <snake_name>s_router
```

2. Antes del healthcheck hay que agregar el app.include
```python
app.include_router(<snake_name>s_router, prefix="/api/v1")
```


## Cómo ejecutar la migración (crear tabla vacía)

En el archivo pyproject.toml ubicar la sección [tool.poe.tasks]

```toml
init_<snake_name>s_table = "python src/modules/<snake_name>s/scripts/create_<snake_name>_table.py"
```

Ahora Poe puede generar la tabla

Powershell
```bash
python -m uv run poe init_<snake_name>s_table
```

En caso de tener instalado **uv** de manera global
```bash
uv run poe init_<snake_name>s_table
```
