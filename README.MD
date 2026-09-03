# Proyecto base para API REST y microservicios con Python

Template de microservicios con FastAPI, PostgreSQL y arquitectura hexagonal de 3 capas,
generado de forma incremental con **GenCLI** (`--hex` + casos de uso `--uc-*`).

## Tabla de contenidos
- Arquitectura hexagonal e incremental [arquitectura.md](doc/arquitectura.md)
- Guía de comandos GenCLI [gencli_comandos.md](doc/gencli_comandos.md)
- Instalación y uso [instalacion.md](doc/instalacion.md)
- Pruebas y TDD [pruebas.md](doc/pruebas.md)
- Calidad del código [calidad.md](doc/calidad.md)
- Migraciones de base de datos [migraciones_db.md](doc/migraciones_db.md)

## Quickstart

```bash
uv sync --dev
# crea .env con PG_USER, PG_PASSWORD, PG_HOST, PG_PORT, PG_DB
# y PAGINATION_CURSOR_SECRET (32+ caracteres) si usas paginación
poe dev
```

Genera un módulo con GenCLI (requiere `gen_config.json` a partir de
`gen_config.example.json`):

```bash
./gen --hex User "nombre:str,email:str"
./gen --uc-list User "nombre:str,email:str"
./gen --uc-create User "nombre:str,email:str"
./gen --uc-get User "nombre:str,email:str"
```

Más comandos y ejemplos en [doc/gencli_comandos.md](doc/gencli_comandos.md).

## Tareas poe

| Tarea | Comando |
|---|---|
| `poe dev` | Servidor con reload en el puerto 8000 |
| `poe start` | Servidor de producción |
| `poe lint` | `ruff check src/ .gen_cli/scripts tests/unit` |
| `poe typecheck` | `mypy src/ .gen_cli/scripts` (estricto) |
| `poe test` | `pytest tests/unit -v` |

La CI (`.github/workflows/ci.yml`) ejecuta las tres puertas de calidad (ruff, mypy,
pytest) en cada push y pull request; los smoke tests ejecutan el binario `./gen`.
