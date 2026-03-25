# Ejecutar migraciones para crear tablas


## Cómo ejecutar la migración (crear tabla vacía)

En el archivo pyproject.toml ubicar la sección [tool.poe.tasks]

Ejemplo:
```toml
init_cosas_table = "python src/modules/cosas/scripts/create_cosa_table.py"
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
