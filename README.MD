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

uv run uvicorn src.main:app --reload