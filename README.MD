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