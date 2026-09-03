"""Elimina un caso de uso generado por GenCLI y limpia todas sus huellas.

Orden de operaciones (fallo seguro): primero se limpian los archivos
compartidos (puerto, adaptador, faker, dependencies, routers, schemas,
main.py) con escritura atómica y validación ``ast``; solo entonces se
eliminan los archivos propios del caso de uso (use case, controller, test).

El script es idempotente: si el caso de uso ya no existe, no modifica nada.
"""

from __future__ import annotations

import argparse
import ast
import re
import shutil
import sys
from pathlib import Path

from register_uc_list import (
    MutationError,
    _find_module_root,
    _find_project_root,
    _write_atomically,
)
from register_uc_get import _append_after_marker  # noqa: F401  (re-export para estabilidad)


# ---------------------------------------------------------------------------
# Catálogo de casos de uso soportados.
#
# Cada entrada define los nombres canónicos que GenCLI genera para ese caso de
# uso.  ``snake`` es el prefijo de archivo (p. ej. ``list`` → ``list_products``)
# y ``entity_prefix`` es el prefijo de clases/funciones (p. ej. ``List`` →
# ``ListProducts``).  ``method`` es el nombre del método del repositorio.
# ``route_path`` es el sufijo de la ruta HTTP (sin el prefix del módulo).
# ---------------------------------------------------------------------------

_USE_CASES: dict[str, dict[str, str]] = {
    "list": {
        "snake": "list",
        "entity_prefix": "List",
        "method": "list",
        "route_decorator": "@router.get(\"/\"",
    },
    "list-paginated": {
        "snake": "list_paginated",
        "entity_prefix": "ListPaginated",
        "method": "list_paginated",
        "route_decorator": "@router.get(\n    \"/paginated\"",
    },
    "find-by": {
        "snake": "find_by",
        "entity_prefix": "FindBy",
        "method": "find_by",
        "route_decorator": "@router.post(\"/find-by\"",
    },
    "create": {
        "snake": "create",
        "entity_prefix": "Create",
        "method": "save",
        "route_decorator": "@router.post(\"/\"",
    },
    "get": {
        "snake": "get",
        "entity_prefix": "Get",
        "method": "find_by_id",
        "route_decorator": "@router.get(\"/{identifier}\"",
    },
    "update": {
        "snake": "update",
        "entity_prefix": "Update",
        "method": "update",
        "route_decorator": "@router.put(\"/{identifier}\"",
    },
    "delete": {
        "snake": "delete",
        "entity_prefix": "Delete",
        "method": "soft_delete",
        "route_decorator": "@router.delete(\"/{identifier}\"",
    },
}


def _to_snake_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def resolve_module_directory(raw_name: str, modules_root: Path) -> Path:
    """Acepta ``User``, ``user`` o ``users`` y devuelve ``src/modules/users``."""
    candidate = raw_name.strip()
    if not candidate or not candidate.isidentifier():
        raise MutationError(f"Nombre de módulo inválido: {raw_name!r}")
    if candidate[0].isupper():
        candidate = _to_snake_case(candidate)
    if not candidate.endswith("s"):
        candidate = f"{candidate}s"
    module_directory = (modules_root / candidate).resolve()
    if module_directory.parent != modules_root.resolve():
        raise MutationError(f"Ruta de módulo fuera de lo permitido: {raw_name!r}")
    if not module_directory.is_dir():
        raise MutationError(
            f"No existe el módulo {module_directory.name!r} en {modules_root}. "
            "Verifica el nombre o lista src/modules/."
        )
    return module_directory


def resolve_use_case(raw_uc: str) -> str:
    """Normaliza el nombre del caso de uso a una clave del catálogo."""
    uc = raw_uc.strip().lower().lstrip("-")
    aliases = {
        "uc-list": "list",
        "uc-list-paginated": "list-paginated",
        "uc-find-by": "find-by",
        "uc-create": "create",
        "uc-get": "get",
        "uc-update": "update",
        "uc-delete": "delete",
    }
    resolved = aliases.get(uc, uc)
    if resolved not in _USE_CASES:
        valid = ", ".join(sorted(_USE_CASES))
        raise MutationError(
            f"Caso de uso desconocido: {raw_uc!r}. Valores válidos: {valid}"
        )
    return resolved


# ---------------------------------------------------------------------------
# Extracción de bloques (funciones, métodos, clases) mediante análisis de
# indentación.  Cada bloque empieza en una línea ``def``/``class``/``async def``
# al nivel de indentación dado y termina cuando aparece una línea con
# indentación menor o igual (no vacía) o fin de archivo.
# ---------------------------------------------------------------------------


def _block_end(lines: list[str], start: int) -> int:
    """Devuelve el índice de la última línea del bloque que empieza en ``start``.

    Un bloque puede tener una firma multilínea con paréntesis abiertos
    (p. ej. ``def foo(`` en una línea y ``) -> T:`` en otra).  Mientras haya
    paréntesis, corchetes o llaves sin cerrar, o hasta que se cierre la firma
    con ``):`` / ``) -> T:``, la línea pertenece a la firma aunque su
    indentación sea menor.
    """
    first_line = lines[start]
    indent = len(first_line) - len(first_line.lstrip())
    end = start
    paren_depth = 0
    signature_closed = False
    for i in range(start, len(lines)):
        line = lines[i]
        if not signature_closed:
            paren_depth += line.count("(") - line.count(")")
            paren_depth += line.count("[") - line.count("]")
            paren_depth += line.count("{") - line.count("}")
            if paren_depth > 0:
                end = i
                continue
            # Sin paréntesis abiertos: si la línea contiene ``:`` la firma
            # terminó aquí; esta línea es parte del bloque.
            if ":" in line:
                signature_closed = True
                end = i
                continue
            # Sin paréntesis y sin ``:`` — no debería pasar en código válido.
            break
        # La firma ya terminó; el cuerpo sigue mientras:
        # - la línea esté vacía (se absorbe), o
        # - tenga indentación mayor que la del ``def``/``class``.
        if line.strip() == "":
            end = i
            continue
        current_indent = len(line) - len(line.lstrip())
        if current_indent <= indent:
            break
        end = i
    return end
    return end


def _remove_blocks(
    content: str, predicates: list[re.Pattern[str]]
) -> tuple[str, int]:
    """Elimina todos los bloques (def/class) cuya primera línea matchea un patrón.

    Retorna ``(contenido_limpio, cantidad_eliminada)``.
    """
    lines = content.splitlines(keepends=True)
    removed = 0
    i = 0
    while i < len(lines):
        stripped = lines[i].lstrip()
        if not (stripped.startswith("def ") or stripped.startswith("async def ") or stripped.startswith("class ")):
            i += 1
            continue
        matched = any(pred.search(lines[i]) for pred in predicates)
        if not matched:
            i += 1
            continue
        end = _block_end(lines, i)
        del lines[i : end + 1]
        removed += 1
        # No avanzar ``i``: la siguiente línea subió a esta posición.
    return "".join(lines), removed


# ---------------------------------------------------------------------------
# Limpieza de imports huérfanos.
#
# Tras eliminar bloques de código, pueden quedar imports que ya nadie usa.
# Hacemos un análisis ingenuo: si un nombre importado (en un ``from X import A, B``)
# no aparece en ninguna otra línea del archivo fuera de los propios imports,
# lo removemos del import.
# ---------------------------------------------------------------------------


def _clean_orphan_from_imports(content: str) -> str:
    """Elimina nombres de imports ``from`` que ya no se usan en el archivo."""
    lines = content.splitlines(keepends=True)
    # Map: line_index -> (module, [names])
    from_imports: dict[int, tuple[str, list[str]]] = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        m = re.match(r"from\s+(?P<mod>[\w.]+)\s+import\s+(?P<names>.+)", stripped)
        if m and ")" not in stripped:
            names = [n.strip() for n in m.group("names").split(",") if n.strip()]
            if names:
                from_imports[i] = (m.group("mod"), names)

    # Construir el cuerpo sin imports para buscar usos.
    import_line_indices = set(from_imports.keys())
    body_lines = [
        line for i, line in enumerate(lines) if i not in import_line_indices
    ]
    body = "".join(body_lines)

    new_lines = list(lines)
    for idx, (module, names) in from_imports.items():
        used: list[str] = []
        for name in names:
            # Buscar el nombre como identificador completo (word boundary).
            if re.search(rf"\b{re.escape(name)}\b", body):
                used.append(name)
        if not used:
            new_lines[idx] = ""  # eliminar import completo
        elif len(used) < len(names):
            flat = f"from {module} import {', '.join(used)}"
            if len(flat) <= 88:
                new_lines[idx] = flat + "\n"
            else:
                wrapped = f"from {module} import (" + "".join(
                    f"\n    {n}," for n in used
                ) + "\n)\n"
                new_lines[idx] = wrapped
    return "".join(new_lines)


def _collapse_blank_lines(content: str) -> str:
    """Colapsa 3+ líneas en blanco consecutivas a 2."""
    return re.sub(r"\n{3,}", "\n\n", content)


# ---------------------------------------------------------------------------
# Limpieza específica por archivo.
# ---------------------------------------------------------------------------


def _clean_port_methods(
    content: str, entity: str, snake: str, method: str
) -> str:
    """Elimina el método del puerto de dominio."""
    pattern = re.compile(
        rf"^\s*async\s+def\s+{re.escape(method)}\b",
    )
    cleaned, _ = _remove_blocks(content, [pattern])
    return cleaned


def _clean_adapter_methods(
    content: str, entity: str, snake: str, method: str
) -> str:
    """Elimina el método del adaptador PostgreSQL."""
    pattern = re.compile(
        rf"^\s*async\s+def\s+{re.escape(method)}\b",
    )
    cleaned, _ = _remove_blocks(content, [pattern])
    return cleaned


def _clean_faker_methods(
    content: str, entity: str, snake: str, method: str
) -> str:
    """Elimina el método del adaptador faker."""
    pattern = re.compile(
        rf"^\s*async\s+def\s+{re.escape(method)}\b",
    )
    cleaned, _ = _remove_blocks(content, [pattern])
    return cleaned


def _clean_dependencies(
    content: str, entity: str, snake: str, entity_prefix: str
) -> str:
    """Elimina el import del use case y la función provider."""
    plural = f"{snake}s"
    plural_entity = f"{entity}s"
    # 1. Eliminar import del use case
    use_case_import = re.compile(
        rf"^from\s+src\.modules\.{plural}\.use_cases\.{entity_prefix.lower()}_{plural}\s+import\s+{entity_prefix}{plural_entity}\s*\n",
        re.MULTILINE,
    )
    cleaned = use_case_import.sub("", content)
    # 2. Eliminar función provider get_<uc>_<plural>
    provider_pattern = re.compile(
        rf"^\s*def\s+get_{entity_prefix.lower()}_{plural}\b",
    )
    cleaned, _ = _remove_blocks(cleaned, [provider_pattern])
    return cleaned


def _clean_schemas(
    content: str, entity: str, snake: str, entity_prefix: str, uc_key: str
) -> str:
    """Elimina las clases de schema y las funciones mapper del caso de uso."""
    plural_entity = f"{entity}s"
    # Nombres de clases y funciones generados por cada UC.
    schema_names: list[str] = []
    if uc_key == "list":
        schema_names = [
            f"{entity}Response",
        ]
    elif uc_key == "list-paginated":
        schema_names = [
            f"{entity}PaginatedItemResponse",
            f"{entity}PaginatedResponse",
        ]
    elif uc_key == "find-by":
        schema_names = [
            f"{entity}FindByQuery",
            f"{entity}FindByRequest",
            f"{entity}FindByItemResponse",
            f"{entity}FindByResponse",
        ]
    elif uc_key == "create":
        schema_names = [
            f"{entity}CreateRequest",
            f"{entity}CreateResponse",
        ]
    elif uc_key == "get":
        schema_names = [
            f"{entity}GetResponse",
        ]
    elif uc_key == "update":
        schema_names = [
            f"{entity}UpdateRequest",
            f"{entity}UpdateResponse",
        ]
    elif uc_key == "delete":
        # delete no genera schemas propios.
        pass

    # Eliminar clases.
    patterns = [re.compile(rf"^\s*class\s+{re.escape(name)}\b") for name in schema_names]
    cleaned, _ = _remove_blocks(content, patterns)

    # Eliminar funciones mapper to_<snake>_*_response.
    mapper_names: list[str] = []
    if uc_key == "list":
        mapper_names = [f"to_{snake}_response"]
    elif uc_key == "list-paginated":
        mapper_names = [f"to_{snake}_paginated_item_response"]
    elif uc_key == "find-by":
        mapper_names = [f"to_{snake}_find_by_item_response"]
    elif uc_key == "create":
        mapper_names = [f"to_{snake}_create_response"]
    elif uc_key == "get":
        mapper_names = [f"to_{snake}_get_response"]
    elif uc_key == "update":
        mapper_names = [f"to_{snake}_update_response"]
    elif uc_key == "delete":
        pass

    mapper_patterns = [
        re.compile(rf"^\s*def\s+{re.escape(name)}\b") for name in mapper_names
    ]
    cleaned, _ = _remove_blocks(cleaned, mapper_patterns)
    return cleaned


def _clean_routes(
    content: str, entity: str, snake: str, entity_prefix: str, uc_key: str
) -> str:
    """Elimina el import del controller/use_case/schemas y el decorador+ruta."""
    plural = f"{snake}s"
    plural_entity = f"{entity}s"
    uc_snake = entity_prefix.lower()

    # 1. Eliminar imports específicos del UC en routers.py.
    #    Controller import:  from .controllers.<uc>_controller import <uc>_controller
    controller_import = re.compile(
        rf"^(from\s+\.controllers\.{uc_snake}_{plural}_controller\s+import\s+{uc_snake}_{plural}_controller)\s*\n",
        re.MULTILINE,
    )
    #    Use case import:    from src.modules.<plural>.use_cases.<uc> import <EntityPrefix><Entity>s
    use_case_import = re.compile(
        rf"^from\s+src\.modules\.{plural}\.use_cases\.{uc_snake}_{plural}\s+import\s+{entity_prefix}{plural_entity}\s*\n",
        re.MULTILINE,
    )
    cleaned = controller_import.sub("", content)
    cleaned = use_case_import.sub("", cleaned)

    # 2. Eliminar imports de schemas específicos del UC.
    schema_names: list[str] = []
    if uc_key == "list":
        schema_names = [f"{entity}Response"]
    elif uc_key == "list-paginated":
        schema_names = [f"{entity}PaginatedResponse"]
    elif uc_key == "find-by":
        schema_names = [f"{entity}FindByRequest", f"{entity}FindByResponse"]
    elif uc_key == "create":
        schema_names = [f"{entity}CreateRequest", f"{entity}CreateResponse"]
    elif uc_key == "get":
        schema_names = [f"{entity}GetResponse"]
    elif uc_key == "update":
        schema_names = [f"{entity}UpdateRequest", f"{entity}UpdateResponse"]
    # delete no importa schemas.
    for name in schema_names:
        # Eliminar el nombre de imports entre paréntesis y planos.
        cleaned = _remove_name_from_imports(cleaned, name)

    # 2b. Eliminar el import del provider get_<uc>_<plural> del bloque
    #     ``from ...dependencies import ( ... )``.
    provider_name = f"get_{uc_snake}_{plural}"
    cleaned = _remove_name_from_imports(cleaned, provider_name)

    # 3. Eliminar el decorador + función de la ruta.
    #    Cada ruta es: @router.<method>(...)  seguido de async def <uc>_<plural>(...
    route_func_pattern = re.compile(
        rf"^\s*async\s+def\s+{uc_snake}_{plural}\b",
    )
    lines = cleaned.splitlines(keepends=True)
    i = 0
    new_lines: list[str] = []
    while i < len(lines):
        # Detectar si esta línea es un decorador que precede a la ruta objetivo.
        stripped = lines[i].strip()
        if stripped.startswith("@router.") and i + 1 < len(lines):
            # Buscar la siguiente línea no vacía que sea ``async def``.
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and route_func_pattern.search(lines[j]):
                # Encontrar el final del bloque de la función.
                func_end = _block_end(lines, j)
                # Saltarse todas las líneas del decorador + función.
                i = func_end + 1
                continue
        new_lines.append(lines[i])
        i += 1
    cleaned = "".join(new_lines)
    return cleaned


def _remove_name_from_imports(content: str, name: str) -> str:
    """Elimina ``name`` de cualquier ``from ... import (...)`` o ``from ... import a, b``."""
    lines = content.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        # Import plano: from X import A, B, C
        flat = re.match(
            r"from\s+(?P<mod>[\w.]+)\s+import\s+(?P<names>.+)", stripped
        )
        if flat and ")" not in stripped and name in flat.group("names"):
            names = [n.strip() for n in flat.group("names").split(",") if n.strip()]
            names = [n for n in names if n != name]
            if not names:
                lines[i] = ""
            else:
                new_line = f"from {flat.group('mod')} import {', '.join(names)}\n"
                lines[i] = new_line
            i += 1
            continue
        # Import entre paréntesis: from X import (\n  A,\n  B,\n)
        if re.match(r"from\s+[\w.]+\s+import\s+\($", stripped):
            end = i + 1
            while end < len(lines) and lines[end].strip() != ")":
                if lines[end].strip().rstrip(",") == name:
                    lines[end] = ""
                end += 1
            # Verificar si quedan nombres.
            remaining = [
                lines[k].strip().rstrip(",")
                for k in range(i + 1, end)
                if lines[k].strip()
            ]
            if not remaining:
                # Eliminar todo el bloque.
                for k in range(i, end + 1):
                    lines[k] = ""
        i += 1
    return "".join(lines)


def _clean_main(content: str, plural: str) -> str:
    """Elimina el import e include_router del módulo de main.py.

    Solo se elimina si después de quitar todos los UCs el router del módulo
    no tiene rutas.  Como este script opera sobre un UC a la vez, NO tocamos
    main.py aquí: el router sigue teniendo otras rutas.  La limpieza de
    main.py la hace ``delete_module.py`` cuando se elimina el módulo entero.
    """
    return content


# ---------------------------------------------------------------------------
# Orquestador principal.
# ---------------------------------------------------------------------------


def delete_use_case(
    module_directory: Path,
    uc_key: str,
    *,
    dry_run: bool,
) -> list[str]:
    """Elimina un caso de uso y todas sus huellas en los archivos compartidos."""
    uc = _USE_CASES[uc_key]
    snake_name = module_directory.name.rstrip("s")
    entity_name = _to_pascal_case(module_directory.name)
    project_root = _find_project_root(module_directory)
    plural = module_directory.name
    plural_entity = f"{entity_name}s"

    # Archivos propios del UC que se eliminarán.
    use_case_file = (
        module_directory / "use_cases" / f"{uc['snake']}_{plural}.py"
    )
    controller_file = (
        module_directory
        / "infrastructure"
        / "http"
        / "controllers"
        / f"{uc['snake']}_{plural}_controller.py"
    )
    test_file = (
        project_root
        / "tests"
        / "unit"
        / "modules"
        / plural
        / f"test_{uc['snake']}_{plural}.py"
    )

    # Archivos compartidos que se limpiarán.
    port_path = module_directory / "domain" / "repositories.py"
    adapter_path = (
        module_directory / "infrastructure" / "persistence" / "repositories.py"
    )
    faker_path = (
        module_directory / "infrastructure" / "persistence" / "faker_repositories.py"
    )
    dependencies_path = (
        module_directory / "infrastructure" / "http" / "dependencies.py"
    )
    router_path = module_directory / "infrastructure" / "http" / "routers.py"
    schemas_path = module_directory / "infrastructure" / "http" / "schemas.py"

    actions: list[str] = []

    # Verificar que el UC existe (al menos el archivo del use case).
    if not use_case_file.is_file():
        actions.append(
            f"El caso de uso '{uc_key}' no existe en {plural} "
            f"(falta {use_case_file.relative_to(project_root)})."
        )
        return actions

    # --- Leer y limpiar archivos compartidos ---
    updates: dict[Path, str] = {}

    if port_path.is_file():
        original = port_path.read_text(encoding="utf-8")
        cleaned = _clean_port_methods(
            original, entity_name, snake_name, uc["method"]
        )
        cleaned = _collapse_blank_lines(cleaned)
        if cleaned != original:
            updates[port_path] = cleaned
            actions.append(
                f"Método '{uc['method']}' removido del puerto: "
                f"{port_path.relative_to(project_root)}"
            )

    if adapter_path.is_file():
        original = adapter_path.read_text(encoding="utf-8")
        cleaned = _clean_adapter_methods(
            original, entity_name, snake_name, uc["method"]
        )
        cleaned = _clean_orphan_from_imports(cleaned)
        cleaned = _collapse_blank_lines(cleaned)
        if cleaned != original:
            updates[adapter_path] = cleaned
            actions.append(
                f"Método '{uc['method']}' removido del adaptador: "
                f"{adapter_path.relative_to(project_root)}"
            )

    if faker_path.is_file():
        original = faker_path.read_text(encoding="utf-8")
        cleaned = _clean_faker_methods(
            original, entity_name, snake_name, uc["method"]
        )
        cleaned = _clean_orphan_from_imports(cleaned)
        cleaned = _collapse_blank_lines(cleaned)
        if cleaned != original:
            updates[faker_path] = cleaned
            actions.append(
                f"Método '{uc['method']}' removido del faker: "
                f"{faker_path.relative_to(project_root)}"
            )

    if dependencies_path.is_file():
        original = dependencies_path.read_text(encoding="utf-8")
        cleaned = _clean_dependencies(
            original, entity_name, snake_name, uc["entity_prefix"]
        )
        cleaned = _clean_orphan_from_imports(cleaned)
        cleaned = _collapse_blank_lines(cleaned)
        if cleaned != original:
            updates[dependencies_path] = cleaned
            actions.append(
                f"Provider e import removidos de dependencies: "
                f"{dependencies_path.relative_to(project_root)}"
            )

    if schemas_path.is_file():
        original = schemas_path.read_text(encoding="utf-8")
        cleaned = _clean_schemas(
            original, entity_name, snake_name, uc["entity_prefix"], uc_key
        )
        cleaned = _clean_orphan_from_imports(cleaned)
        cleaned = _collapse_blank_lines(cleaned)
        if cleaned != original:
            updates[schemas_path] = cleaned
            actions.append(
                f"Schemas y mappers removidos: "
                f"{schemas_path.relative_to(project_root)}"
            )

    if router_path.is_file():
        original = router_path.read_text(encoding="utf-8")
        cleaned = _clean_routes(
            original, entity_name, snake_name, uc["entity_prefix"], uc_key
        )
        cleaned = _clean_orphan_from_imports(cleaned)
        cleaned = _collapse_blank_lines(cleaned)
        if cleaned != original:
            updates[router_path] = cleaned
            actions.append(
                f"Ruta e imports removidos del router: "
                f"{router_path.relative_to(project_root)}"
            )

    # --- Escribir cambios atómicos ---
    if updates and not dry_run:
        _write_atomically(updates)

    # --- Eliminar archivos propios del UC ---
    for file_path in (use_case_file, controller_file, test_file):
        if file_path.is_file():
            relative = file_path.relative_to(project_root)
            actions.append(f"Archivo eliminado: {relative}")
            if not dry_run:
                file_path.unlink()

    return actions


def _to_pascal_case(name: str) -> str:
    """Convierte ``users`` → ``User``, ``api_keys`` → ``ApiKey``."""
    singular = name.rstrip("s")
    return "".join(part.capitalize() for part in singular.split("_"))


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Elimina un caso de uso generado por GenCLI de un módulo "
            "y limpia todas sus huellas (puerto, adaptador, faker, "
            "dependencies, schemas, router, controller, test)."
        ),
    )
    parser.add_argument("module", help="Nombre del módulo: User, user o users")
    parser.add_argument(
        "use_case",
        help=(
            "Caso de uso a eliminar: list, list-paginated, find-by, "
            "create, get, update, delete (o --uc-list, etc.)"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra lo que se eliminaría sin modificar nada.",
    )
    args = parser.parse_args()

    try:
        project_root = _find_project_root(Path.cwd())
        module_directory = resolve_module_directory(
            args.module, project_root / "src" / "modules"
        )
        uc_key = resolve_use_case(args.use_case)
        actions = delete_use_case(
            module_directory, uc_key, dry_run=args.dry_run
        )
    except MutationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not actions:
        actions.append("No se encontraron cambios que aplicar.")

    prefix = "[dry-run] " if args.dry_run else ""
    for action in actions:
        print(f"{prefix}{action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())