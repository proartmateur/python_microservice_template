# Cómo usar el módulo

Para que las rutas de API funcionen es necesario agregar en main.py
el router del módulo.

1. Importar en los encabezados de main el router
```python
from src.modules.users.infrastructure.http.routers import router as users_router
```

2. Antes del healthcheck hay que agregar el app.include

1. Importar en los encabezados de main el router
```python
app.include_router(users_router, prefix="/api/v1")
```


## Cómo ejecutar la migración (crear tabla vacía)

En el archivo pyproject.toml ubicar la sección [tool.poe.tasks]

```toml
init_users_table = "python src/modules/users/scripts/create_user_table.py"
```

Ahora Poe puede generar la tabla

Powershell
```bash
python -m uv run poe init_cosas_table
```

En caso de tener instalado **uv** de manera global
```bash
uv run poe init_cosas_table
```
