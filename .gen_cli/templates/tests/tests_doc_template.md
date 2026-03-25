# ¿Cómo ejecutar los test del módulo <ent>s?

1.- Agregar al archivo pyproject.toml
la siguiente línea en la sección [tool.poe.tasks]

```toml
[tool.poe.tasks]
test_e2e_<snake_name>s = "pytest tests/e2e/<snake_name>s -m e2e -v"
```

Esto permitirá que poe pueda ejecutar los test.

## En windows con Powershell
1. Establecer una variable de entorno local, sin este paso
pytest no va a correr los test.


```bash
$env:RUN_E2E_$const_name$S="1"
```

**¿Porqué?**

Como una medida de seguridad para prevenir correr test contra una base de datos productiva,
es que esta variable de entorno esté activa solamente en modo desarrollo cuando
se esté desarrollando con una base de datos de desarrollo.

Los test CRUD implican Crear y **ELIMINAR** registros de las tablas y será terrible
afectar una base de datos productiva.

2. Ejecutar los test del módulo

```bash
python -m uv run poe test_e2e_<snake_name>s
```

En el caso de tener funcionando **uv** como una dependencia global basta con ejecutar:

```bash
uv run poe test_e2e_<snake_name>s
```
