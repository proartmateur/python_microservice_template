# Instalación y uso

## Requisitos previos

### Requisitos obligatorios
- Python 3.12 o superior
- pip (gestor de paquetes de Python)
- uv (gestor de entornos y tareas)
- genCLI 2.1+ [genCLI](https://github.com/proartmateur/gen_v2)

### Opcionales pero recomendados
- Un editor de código (recomendado: Visual Studio Code)
- Git (opcional, para clonar el repositorio)
- Docker (opcional, para ejecutar el proyecto en contenedores)
- PostgreSQL (opcional, para usar la base de datos relacional)

## Instalación

### Usar uv

Instalar uv:
```bash
pip install uv
```

Probar UV
```bash
uv --version
``` 

En caso de que no se pueda usar el comando uv directamente:

```bash
python -m uv
```

### Instalar dependencias

```bash
uv sync --all-extras
```


## Ejecutar el proyecto

Ejecutar en modo desarrollo

```bash
uv run poe dev
```

### Modo faker (sin base de datos)

Si no tienes PostgreSQL disponible o aún no has modelado el esquema, puedes
arrancar la API con datos sintéticos en memoria:

1. Crea un `.env` (o exporta las variables) con:

```env
REPOSITORY_DATA_SOURCE=faker
```

   No se requieren credenciales `PG_*` en este modo. El
   `PAGINATION_CURSOR_SECRET` es opcional: si no se define, se genera uno
   efímero por arranque (suficiente para desarrollo).

2. Arranca como siempre:

```bash
uv run poe dev
```

La API funcionará con todos los endpoints CRUD, pero los datos viven solo en
memoria y se pierden al detener el proceso. **No usar en producción.**

### Modo database (PostgreSQL)

Requiere un `.env` con las credenciales de PostgreSQL:

```env
REPOSITORY_DATA_SOURCE=database
PG_USER=...
PG_PASSWORD=...
PG_HOST=...
PG_PORT=5432
PG_DB=...
PAGINATION_CURSOR_SECRET=<32+ caracteres>
```

Es el comportamiento por defecto si no se define `REPOSITORY_DATA_SOURCE`.

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
- `PUT /api/v1/users/{user_id}` actualiza un usuario
- `DELETE /api/v1/users/{user_id}` aplica soft delete

## Ejecutar en modo productivo

```bash
uv run poe start
```