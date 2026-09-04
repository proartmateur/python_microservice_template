"""Genera un caso de uso custom con SQL raw de PostgreSQL.

Produce un endpoint vertical completo (controller, use case, repository custom,
schemas, ruta, test) que ejecuta una consulta SQL nativa de forma segura con
parámetros tipados. Pensado para consumir vistas, stored procedures, joins,
agregaciones u otras consultas que no encajan en el patrón CRUD del generador.

Uso:
    poe gen_custom_query <Module> --route <route> --method <GET|POST> \
        --sql "<sql>" [--params "name:type,..."] [--dry-run]

    poe gen_custom_query <Module> --route <route> --method <GET|POST> \
        --sql-file <path> [--params "name:type,..."] [--dry-run]
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

from register_uc_list import (
    MutationError,
    _find_module_root,
    _find_project_root,
    _insert_after_marker,
    _read_required,
    _write_atomically,
)
from delete_use_case import resolve_module_directory
from delete_module import _to_snake_case

# ---------------------------------------------------------------------------
# Tipos Python soportados para los parámetros.
# ---------------------------------------------------------------------------

_PYTHON_TYPES: dict[str, str] = {
    "str": "str",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "datetime": "datetime",
    "UUID": "UUID",
}

_TYPE_IMPORTS: dict[str, str] = {
    "datetime": "from datetime import datetime",
    "UUID": "from uuid import UUID",
}


# ---------------------------------------------------------------------------
# Parsing de parámetros.
# ---------------------------------------------------------------------------


def _parse_params(inline_params: str) -> list[tuple[str, str]]:
    """Convierte ``"region:str,month:int"`` → ``[("region", "str"), ("month", "int")]``."""
    params: list[tuple[str, str]] = []
    if not inline_params.strip():
        return params
    for item in inline_params.split(","):
        item = item.strip()
        if not item:
            continue
        name, sep, ptype = item.partition(":")
        if not sep or not name.isidentifier():
            raise MutationError(f"Parámetro inválido: {item!r}")
        ptype = ptype.strip()
        if ptype not in _PYTHON_TYPES:
            raise MutationError(
                f"Tipo no soportado: {ptype!r}. Valores válidos: "
                f"{', '.join(sorted(_PYTHON_TYPES))}"
            )
        params.append((name, _PYTHON_TYPES[ptype]))
    return params


def _route_to_snake(route: str) -> str:
    """Convierte ``sales-by-region`` → ``sales_by_region``."""
    return re.sub(r"[^a-zA-Z0-9]+", "_", route).strip("_").lower()


def _route_to_pascal(route: str) -> str:
    """Convierte ``sales-by-region`` → ``SalesByRegion``."""
    return "".join(part.capitalize() for part in re.split(r"[^a-zA-Z0-9]+", route) if part)


def _indent_sql(sql: str, indent: str = "            ") -> str:
    """Indenta cada línea del SQL para embeberlo en un string triple-quote."""
    lines = sql.strip().splitlines()
    return "\n".join(f"{indent}{line}" for line in lines)


# ---------------------------------------------------------------------------
# Generación de archivos.
# ---------------------------------------------------------------------------


def _generate_use_case(
    module_snake: str,
    module_pascal: str,
    route_snake: str,
    route_pascal: str,
    params: list[tuple[str, str]],
) -> str:
    """Genera el caso de uso que orquesta la consulta custom."""
    param_names = [name for name, _ in params]
    method_name = route_snake

    if param_names:
        param_signature = ", ".join(f"{name}: {ptype}" for name, ptype in params)
        param_call = ", ".join(f"{name}={name}" for name in param_names)
        repo_call = f"await self._repository.{method_name}({param_call})"
    else:
        param_signature = ""
        param_call = ""
        repo_call = f"await self._repository.{method_name}()"

    type_imports = "\n".join(
        _TYPE_IMPORTS[ptype] for _, ptype in params if ptype in _TYPE_IMPORTS
    )
    if type_imports:
        type_imports = f"\n{type_imports}"

    return f'''"""Caso de uso custom: ejecuta una consulta SQL nativa."""

from __future__ import annotations

from dataclasses import dataclass

from src.modules.{module_snake}s.infrastructure.persistence.custom_repositories import (
    Custom{module_pascal}Repository,
)
{type_imports}


@dataclass(frozen=True)
class Custom{route_pascal}Result:
    """Resultado de la consulta custom como lista de diccionarios."""
    rows: list[dict[str, object]]


class Custom{route_pascal}:
    """Caso de uso que orquesta una consulta SQL nativa via repositorio custom."""

    def __init__(self, repository: Custom{module_pascal}Repository) -> None:
        self._repository = repository

    async def execute(self{", " + param_signature if param_signature else ""}) -> Custom{route_pascal}Result:
        rows = {repo_call}
        return Custom{route_pascal}Result(rows=rows)
'''


def _generate_controller(
    module_snake: str,
    module_pascal: str,
    route_snake: str,
    route_pascal: str,
    params: list[tuple[str, str]],
) -> str:
    """Genera el controller HTTP que traduce la petición al caso de uso."""
    param_names = [name for name, _ in params]

    if param_names:
        param_call = ", ".join(f"{name}=request.{name}" for name in param_names)
        schema_imports = (
            f"from src.modules.{module_snake}s.infrastructure.http.schemas import (\n"
            f"    Custom{route_pascal}Request,\n"
            f"    Custom{route_pascal}Response,\n"
            f")"
        )
        signature = (
            f"async def custom_{route_snake}_controller(\n"
            f"    use_case: Custom{route_pascal},\n"
            f"    request: Custom{route_pascal}Request,\n"
            f") -> Custom{route_pascal}Response:"
        )
        execute_line = f"    result = await use_case.execute({param_call})"
    else:
        schema_imports = (
            f"from src.modules.{module_snake}s.infrastructure.http.schemas import (\n"
            f"    Custom{route_pascal}Response,\n"
            f")"
        )
        signature = (
            f"async def custom_{route_snake}_controller(\n"
            f"    use_case: Custom{route_pascal},\n"
            f") -> Custom{route_pascal}Response:"
        )
        execute_line = "    result = await use_case.execute()"

    return f'''"""Controller HTTP para el caso de uso custom {route_snake}."""

from __future__ import annotations

from src.modules.{module_snake}s.use_cases.custom_{route_snake} import (
    Custom{route_pascal},
)
{schema_imports}

{signature}
{execute_line}
    return Custom{route_pascal}Response(rows=result.rows)
'''


def _generate_custom_repository(
    module_snake: str,
    module_pascal: str,
    route_snake: str,
    route_pascal: str,
    sql: str,
    params: list[tuple[str, str]],
    existing_content: str | None = None,
) -> str:
    """Genera o extiende el repositorio custom con el método para esta consulta."""
    param_names = [name for name, _ in params]

    # Construir el cuerpo del método.
    # Siempre usar una variable _sql para evitar líneas demasiado largas.
    if param_names:
        param_signature = ", *, " + ", ".join(
            f"{name}: {ptype}" for name, ptype in params
        )
        param_dict = "{" + ", ".join(f'"{name}": {name}' for name in param_names) + "}"
        body = (
            f'        _sql = text("""\n'
            f"{_indent_sql(sql)}\n"
            f'        """)\n'
            f"        result = await self._session.execute(_sql, {param_dict})\n"
        )
    else:
        param_signature = ""
        body = (
            f'        _sql = text("""\n'
            f"{_indent_sql(sql)}\n"
            f'        """)\n'
            f"        result = await self._session.execute(_sql)\n"
        )

    method = f'''    async def {route_snake}(self{param_signature}) -> list[dict[str, object]]:
        """Consulta SQL nativa generada por gen_custom_query."""
{body}        return [dict(row) for row in result.mappings().all()]'''

    if existing_content is None:
        # Crear archivo nuevo.
        return f'''"""Repositorio custom para consultas SQL nativas de {module_snake}s.

Este repositorio ejecuta SQL directo a PostgreSQL mediante SQLAlchemy ``text()``.
Los parámetros siempre van parameterized (``:param``) para evitar inyección SQL.
"""

# SQL embebido puede exceder el límite de línea; es confianza de desarrollador.
# ruff: noqa: E501

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class Custom{module_pascal}Repository:
    """Repositorio custom para consultas SQL nativas del módulo {module_pascal}."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # gencli:custom-repository-methods
{method}
'''

    # Extender archivo existente: insertar tras el marcador.
    marker = "# gencli:custom-repository-methods"
    if marker not in existing_content:
        raise MutationError(
            f"No se encontró el marcador {marker!r} en custom_repositories.py"
        )
    if f"async def {route_snake}(" in existing_content:
        # Ya existe, no duplicar.
        return existing_content
    return existing_content.replace(
        marker, f"{marker}\n{method}", 1
    )


def _generate_request_schema(
    module_pascal: str,
    route_pascal: str,
    params: list[tuple[str, str]],
) -> str:
    """Genera el schema Pydantic de petición con los parámetros tipados."""
    if not params:
        return ""

    type_imports = "\n".join(
        _TYPE_IMPORTS[ptype] for _, ptype in params if ptype in _TYPE_IMPORTS
    )
    if type_imports:
        type_imports = f"\n{type_imports}\n"

    fields = "\n".join(f"    {name}: {ptype}" for name, ptype in params)

    return f'''{type_imports}
class Custom{route_pascal}Request(BaseModel):
    model_config = ConfigDict(strict=True)
{fields}
'''


def _generate_response_schema(module_pascal: str, route_pascal: str) -> str:
    """Genera el schema de respuesta con rows como lista de diccionarios."""
    return f'''
class Custom{route_pascal}Response(BaseModel):
    rows: list[dict[str, object]]
'''


def _generate_test(
    module_snake: str,
    module_pascal: str,
    route_snake: str,
    route_pascal: str,
    params: list[tuple[str, str]],
) -> str:
    """Genera el test unitario con fake repository."""
    param_names = [name for name, _ in params]
    if param_names:
        param_args = ", ".join(f'{name}="test"' for name in param_names)
        execute_call = f"await use_case.execute({param_args})"
    else:
        execute_call = "await use_case.execute()"

    return f'''"""Test unitario del caso de uso custom {route_snake}."""

import pytest

from src.modules.{module_snake}s.use_cases.custom_{route_snake} import (
    Custom{route_pascal},
)


class FakeCustom{module_pascal}Repository:
    """Fake del repositorio custom para tests sin DB."""

    async def {route_snake}(self{", *, " + ", ".join(f"{n}: str" for n in param_names) if param_names else ""}) -> list[dict[str, object]]:
        return [{{"sample_field": "sample_value"}}]


@pytest.mark.asyncio
async def test_custom_{route_snake}_returns_rows() -> None:
    repository = FakeCustom{module_pascal}Repository()
    use_case = Custom{route_pascal}(repository)
    result = {execute_call}
    assert result.rows is not None
    assert len(result.rows) >= 1
    assert "sample_field" in result.rows[0]
'''


# ---------------------------------------------------------------------------
# Inyección en archivos compartidos.
# ---------------------------------------------------------------------------


def _inject_dependencies(
    content: str,
    module_snake: str,
    module_pascal: str,
    route_snake: str,
    route_pascal: str,
) -> str:
    """Inyecta el import del use case y el provider en dependencies.py."""
    # Import del repositorio custom.
    content = _insert_after_marker(
        content,
        "# gencli:use-case-imports",
        f"from src.modules.{module_snake}s.infrastructure.persistence.custom_repositories import Custom{module_pascal}Repository",
    )
    # Import del use case.
    content = _insert_after_marker(
        content,
        "# gencli:use-case-imports",
        f"from src.modules.{module_snake}s.use_cases.custom_{route_snake} import Custom{route_pascal}",
    )
    # Import de la sesión de DB.
    content = _insert_after_marker(
        content,
        "# gencli:use-case-imports",
        "from src.shared.infrastructure.persistence.database import get_db_session",
    )
    # Provider.
    content = _insert_after_marker(
        content,
        "# gencli:use-case-providers",
        f"def get_custom_{route_snake}(\n    session: AsyncSession = Depends(get_db_session),\n) -> Custom{route_pascal}:\n    return Custom{route_pascal}(Custom{module_pascal}Repository(session))",
    )
    return content


def _inject_schemas(
    content: str,
    route_pascal: str,
    params: list[tuple[str, str]],
) -> str:
    """Inyecta los schemas de request y response en schemas.py."""
    # Imports necesarios.
    content = _insert_after_marker(
        content,
        "# gencli:schema-imports",
        "from pydantic import BaseModel, ConfigDict",
    )
    # Request schema (solo si hay parámetros).
    request_schema = _generate_request_schema("", route_pascal, params)
    if request_schema.strip():
        content = _insert_after_marker(
            content,
            "# gencli:schema-models",
            request_schema,
        )
    # Response schema.
    response_schema = _generate_response_schema("", route_pascal)
    content = _insert_after_marker(
        content,
        "# gencli:schema-models",
        response_schema,
    )
    return content


def _inject_router(
    content: str,
    module_snake: str,
    module_pascal: str,
    route_snake: str,
    route_pascal: str,
    method: str,
    route_path: str,
    has_params: bool,
) -> str:
    """Inyecta imports y ruta en routers.py."""
    plural = f"{module_snake}s"

    # Imports.
    content = _insert_after_marker(
        content,
        "# gencli:router-imports",
        f"from .controllers.custom_{route_snake}_controller import custom_{route_snake}_controller",
    )
    content = _insert_after_marker(
        content,
        "# gencli:router-imports",
        f"from src.modules.{plural}.infrastructure.http.dependencies import get_custom_{route_snake}",
    )
    if has_params:
        content = _insert_after_marker(
            content,
            "# gencli:router-imports",
            f"from src.modules.{plural}.infrastructure.http.schemas import Custom{route_pascal}Request, Custom{route_pascal}Response",
        )
    else:
        content = _insert_after_marker(
            content,
            "# gencli:router-imports",
            f"from src.modules.{plural}.infrastructure.http.schemas import Custom{route_pascal}Response",
        )
    content = _insert_after_marker(
        content,
        "# gencli:router-imports",
        f"from src.modules.{plural}.use_cases.custom_{route_snake} import Custom{route_pascal}",
    )

    # Ruta.
    if has_params:
        route = (
            f'@router.{method.lower()}("/{route_path}", response_model=Custom{route_pascal}Response)\n'
            f"async def custom_{route_snake}(\n"
            f"    request: Custom{route_pascal}Request,\n"
            f"    use_case: Annotated[Custom{route_pascal}, Depends(get_custom_{route_snake})],\n"
            f") -> Custom{route_pascal}Response:\n"
            f"    return await custom_{route_snake}_controller(use_case, request)"
        )
    else:
        route = (
            f'@router.{method.lower()}("/{route_path}", response_model=Custom{route_pascal}Response)\n'
            f"async def custom_{route_snake}(\n"
            f"    use_case: Annotated[Custom{route_pascal}, Depends(get_custom_{route_snake})],\n"
            f") -> Custom{route_pascal}Response:\n"
            f"    return await custom_{route_snake}_controller(use_case)"
        )

    # Las rutas custom se añaden al final (tras las dinámicas).
    return content.rstrip() + "\n\n" + route + "\n"


# ---------------------------------------------------------------------------
# Orquestador.
# ---------------------------------------------------------------------------


def generate_custom_query(
    module_directory: Path,
    route: str,
    method: str,
    sql: str,
    inline_params: str,
    *,
    dry_run: bool,
) -> list[str]:
    """Genera un caso de uso custom con SQL raw."""
    module_name = module_directory.name
    module_snake = module_name.rstrip("s")
    module_pascal = "".join(
        part.capitalize() for part in module_snake.split("_")
    )
    route_snake = _route_to_snake(route)
    route_pascal = _route_to_pascal(route)
    params = _parse_params(inline_params)
    project_root = _find_project_root(module_directory)

    # Normalizar SQL: strip pero mantener estructura multilínea.
    sql = sql.strip()

    # Validar que el SQL no sea vacío.
    if not sql:
        raise MutationError("La consulta SQL no puede estar vacía.")

    # Validar parámetros: todo :param en el SQL debe estar en la lista de params.
    sql_params = set(re.findall(r":(\w+)", sql))
    declared_params = {name for name, _ in params}
    # Excluir dobles :: (cast de Postgres como ::int).
    sql_params = {p for p in sql_params if not sql.count(f"::{p}")}
    missing = sql_params - declared_params
    if missing:
        raise MutationError(
            f"El SQL tiene parámetros no declarados: {', '.join(sorted(missing))}. "
            f"Añádelos con --params."
        )

    # Rutas de archivos.
    use_case_path = (
        module_directory / "use_cases" / f"custom_{route_snake}.py"
    )
    controller_path = (
        module_directory
        / "infrastructure"
        / "http"
        / "controllers"
        / f"custom_{route_snake}_controller.py"
    )
    custom_repo_path = (
        module_directory
        / "infrastructure"
        / "persistence"
        / "custom_repositories.py"
    )
    test_path = (
        project_root
        / "tests"
        / "unit"
        / "modules"
        / module_name
        / f"test_custom_{route_snake}.py"
    )
    dependencies_path = (
        module_directory / "infrastructure" / "http" / "dependencies.py"
    )
    schemas_path = (
        module_directory / "infrastructure" / "http" / "schemas.py"
    )
    router_path = (
        module_directory / "infrastructure" / "http" / "routers.py"
    )

    actions: list[str] = []

    # --- Leer archivos compartidos ---
    documents = _read_required((dependencies_path, schemas_path, router_path))

    # --- Generar archivos nuevos ---
    use_case_code = _generate_use_case(
        module_snake, module_pascal, route_snake, route_pascal, params
    )
    controller_code = _generate_controller(
        module_snake, module_pascal, route_snake, route_pascal, params
    )
    test_code = _generate_test(
        module_snake, module_pascal, route_snake, route_pascal, params
    )

    # --- Generar/extender repositorio custom ---
    existing_repo = None
    if custom_repo_path.is_file():
        existing_repo = custom_repo_path.read_text(encoding="utf-8")
    custom_repo_code = _generate_custom_repository(
        module_snake, module_pascal, route_snake, route_pascal,
        sql, params, existing_repo,
    )

    # --- Inyectar en archivos compartidos ---
    documents[dependencies_path] = _inject_dependencies(
        documents[dependencies_path], module_snake, module_pascal,
        route_snake, route_pascal,
    )
    documents[schemas_path] = _inject_schemas(
        documents[schemas_path], route_pascal, params,
    )
    documents[router_path] = _inject_router(
        documents[router_path], module_snake, module_pascal,
        route_snake, route_pascal, method, route, bool(params),
    )

    # --- Validar con ast.parse antes de escribir ---
    all_writes: dict[Path, str] = {}
    all_writes[use_case_path] = use_case_code
    all_writes[controller_path] = controller_code
    all_writes[custom_repo_path] = custom_repo_code
    all_writes[test_path] = test_code
    all_writes.update(documents)

    # Validar sintaxis Python de todo.
    for path, code in all_writes.items():
        try:
            ast.parse(code, filename=str(path))
        except SyntaxError as exc:
            raise MutationError(
                f"Error de sintaxis en {path}: {exc}"
            ) from exc

    # --- Reportar acciones ---
    if existing_repo is None:
        actions.append(f"Archivo creado: {custom_repo_path.relative_to(project_root)}")
    else:
        actions.append(f"Método añadido a: {custom_repo_path.relative_to(project_root)}")
    actions.append(f"Archivo creado: {use_case_path.relative_to(project_root)}")
    actions.append(f"Archivo creado: {controller_path.relative_to(project_root)}")
    actions.append(f"Archivo creado: {test_path.relative_to(project_root)}")
    actions.append(f"Inyección en: {dependencies_path.relative_to(project_root)}")
    actions.append(f"Inyección en: {schemas_path.relative_to(project_root)}")
    actions.append(f"Inyección en: {router_path.relative_to(project_root)}")
    actions.append(
        f"Ruta generada: {method.upper()} /api/v1/{module_name}/{route}"
    )

    if not dry_run:
        # Escribir archivos nuevos.
        for path in (use_case_path, controller_path, test_path, custom_repo_path):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(all_writes[path], encoding="utf-8")
        # Escribir archivos compartidos atómicamente.
        _write_atomically(documents)

    return actions


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Genera un caso de uso custom con SQL raw de PostgreSQL. "
            "Produce un endpoint vertical completo (controller, use case, "
            "repository custom, schemas, ruta, test)."
        ),
    )
    parser.add_argument("module", help="Nombre del módulo: Product, product o products")
    parser.add_argument("--route", required=True, help="Nombre de la ruta (ej: sales-by-region)")
    parser.add_argument("--method", required=True, choices=["GET", "POST", "PUT", "DELETE"], help="Método HTTP")
    parser.add_argument("--sql", help="Consulta SQL inline")
    parser.add_argument("--sql-file", help="Ruta a archivo .sql con la consulta")
    parser.add_argument("--params", default="", help='Parámetros tipados: "region:str,month:int"')
    parser.add_argument("--dry-run", action="store_true", help="Preview sin modificar nada")
    args = parser.parse_args()

    try:
        project_root = _find_project_root(Path.cwd())
        module_directory = resolve_module_directory(
            args.module, project_root / "src" / "modules"
        )

        # Obtener SQL.
        if args.sql_file:
            sql_path = Path(args.sql_file)
            if not sql_path.is_file():
                print(f"Error: no existe el archivo SQL: {sql_path}", file=sys.stderr)
                return 1
            sql = sql_path.read_text(encoding="utf-8")
        elif args.sql:
            sql = args.sql
        else:
            print("Error: debe proporcionar --sql o --sql-file", file=sys.stderr)
            return 1

        actions = generate_custom_query(
            module_directory,
            args.route,
            args.method,
            sql,
            args.params,
            dry_run=args.dry_run,
        )
    except MutationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    prefix = "[dry-run] " if args.dry_run else ""
    for action in actions:
        print(f"{prefix}{action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())