"""Elimina un módulo generado por GenCLI y limpia ``src/main.py``.

Orden de operaciones (fallo seguro): primero se limpia ``main.py`` con
escritura atómica y validación ``ast``; solo entonces se eliminan los
directorios del módulo y de sus pruebas.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from register_uc_list import MutationError, _find_project_root, _write_atomically


def _to_snake_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def resolve_module_directory(raw_name: str, modules_root: Path) -> Path:
    """Acepta ``User``, ``user`` o ``users`` y devuelve ``src/modules/users``."""
    candidate = raw_name.strip()
    if not candidate.isidentifier():
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


def _remove_module_references(main_content: str, module: str) -> str:
    import_pattern = re.compile(
        rf"^from src\.modules\.{module}\.[^\n]*\n", re.MULTILINE
    )
    include_pattern = re.compile(
        rf"^[ \t]*app\.include_router\({module}_router[^\n]*\n", re.MULTILINE
    )
    cleaned = import_pattern.sub("", main_content)
    cleaned = include_pattern.sub("", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned)


def delete_module(module_directory: Path, *, dry_run: bool) -> list[str]:
    """Elimina el módulo, sus pruebas y sus referencias en ``main.py``."""
    project_root = _find_project_root(module_directory)
    module = module_directory.name
    actions: list[str] = []

    main_path = project_root / "src" / "main.py"
    if main_path.is_file():
        main_content = main_path.read_text(encoding="utf-8")
        cleaned = _remove_module_references(main_content, module)
        if cleaned != main_content:
            actions.append("Referencias removidas de src/main.py")
            if not dry_run:
                _write_atomically({main_path: cleaned})

    candidates_to_remove = [
        module_directory,
        project_root / "tests" / "unit" / "modules" / module,
        project_root / "tests" / "e2e" / module,
    ]
    for candidate in candidates_to_remove:
        if candidate.is_dir():
            relative = candidate.relative_to(project_root)
            actions.append(f"Directorio eliminado: {relative}")
            if not dry_run:
                shutil.rmtree(candidate)

    if not actions:
        actions.append("El módulo no tenía referencias en main.py ni pruebas.")
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Elimina un módulo generado y limpia main.py."
    )
    parser.add_argument("module", help="Nombre del módulo: User, user o users")
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
        actions = delete_module(module_directory, dry_run=args.dry_run)
    except MutationError as exc:
        print(f"Error al eliminar el módulo: {exc}", file=sys.stderr)
        return 1

    prefix = "[dry-run] " if args.dry_run else ""
    for action in actions:
        print(f"{prefix}{action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
