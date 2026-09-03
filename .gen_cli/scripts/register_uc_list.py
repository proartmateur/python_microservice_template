"""Completa los contratos base después de generar ``--uc-list``."""

from __future__ import annotations

import ast
import os
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path


class MutationError(RuntimeError):
    """Indica que un archivo no cumple el contrato de mutación de GenCLI."""


def _insert_after_marker(document: str, marker: str, addition: str) -> str:
    if addition in document:
        return document
    if marker not in document:
        raise MutationError(f"No se encontró el marcador requerido: {marker}")
    return document.replace(marker, f"{marker}\n{addition}", 1)


def _parse_properties(inline_properties: str) -> list[str]:
    properties: list[str] = []
    for item in filter(None, (part.strip() for part in inline_properties.split(","))):
        name, separator, _ = item.partition(":")
        if not separator or not name.isidentifier():
            raise MutationError(f"Propiedad inválida: {item!r}")
        properties.append(name)
    if not properties:
        raise MutationError("--uc-list requiere al menos una propiedad tipada.")
    return properties


def _find_project_root(module_root: Path) -> Path:
    for candidate in (module_root, *module_root.parents):
        if (candidate / "src" / "main.py").is_file():
            return candidate
    raise MutationError("No se encontró src/main.py desde el módulo generado.")


def _find_module_root(generated_file: Path) -> Path:
    for candidate in (generated_file.parent, *generated_file.parents):
        if (candidate / "domain" / "repositories.py").is_file():
            return candidate
    raise MutationError(
        "No se encontró el módulo base. Ejecute --hex antes de --uc-list."
    )


def _read_required(paths: Iterable[Path]) -> dict[Path, str]:
    contents: dict[Path, str] = {}
    for path in paths:
        if not path.is_file():
            raise MutationError(f"No existe el archivo requerido: {path}")
        contents[path] = path.read_text(encoding="utf-8")
    return contents


def _write_atomically(updates: dict[Path, str]) -> None:
    for path, content in updates.items():
        ast.parse(content, filename=str(path))

    temporary_files: dict[Path, Path] = {}
    try:
        for path, content in updates.items():
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_file.write(content)
                temporary_files[path] = Path(temporary_file.name)

        for path, temporary_path in temporary_files.items():
            os.replace(temporary_path, path)
    finally:
        for temporary_path in temporary_files.values():
            temporary_path.unlink(missing_ok=True)


def register_list(
    generated_use_case: Path,
    entity_name: str,
    snake_name: str,
    inline_properties: str,
) -> None:
    properties = _parse_properties(inline_properties)
    module_root = _find_module_root(generated_use_case.resolve())
    plural_name = f"{snake_name}s"
    plural_entity = f"{entity_name}s"
    project_root = _find_project_root(module_root)

    port_path = module_root / "domain" / "repositories.py"
    adapter_path = module_root / "infrastructure" / "persistence" / "repositories.py"
    dependencies_path = module_root / "infrastructure" / "http" / "dependencies.py"
    router_path = module_root / "infrastructure" / "http" / "routers.py"
    main_path = project_root / "src" / "main.py"
    documents = _read_required(
        (port_path, adapter_path, dependencies_path, router_path, main_path)
    )

    entity_import = (
        f"from src.modules.{plural_name}.domain.entities import {entity_name}Entity"
    )
    model_import = (
        f"from src.modules.{plural_name}.infrastructure.persistence.models import "
        f"{entity_name}Model"
    )
    use_case_import = (
        f"from src.modules.{plural_name}.use_cases.list_{plural_name} import "
        f"List{plural_entity}"
    )
    entity_constructor = ",\n            ".join(
        [f"id_{snake_name}=db_{snake_name}.id_{snake_name}"]
        + [
            f"{property_name}=db_{snake_name}.{property_name}"
            for property_name in properties
        ]
        + [f"created_at=db_{snake_name}.created_at"]
    )

    documents[port_path] = _insert_after_marker(
        documents[port_path],
        "# gencli:repository-port-imports",
        entity_import,
    )
    documents[port_path] = _insert_after_marker(
        documents[port_path],
        "# gencli:repository-port-methods",
        (
            f"    async def list(self, *, limit: int) -> list[{entity_name}Entity]:\n"
            '        """Devuelve una colección acotada de entidades activas."""\n'
            "        ..."
        ),
    )

    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path],
        "# gencli:repository-adapter-imports",
        f"from sqlalchemy import select\n{entity_import}\n{model_import}",
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path],
        "# gencli:repository-adapter-methods",
        (
            f"    async def list(self, *, limit: int) -> list[{entity_name}Entity]:\n"
            f"        statement = (\n"
            f"            select({entity_name}Model)\n"
            f"            .where({entity_name}Model.deleted_at.is_(None))\n"
            "            .order_by(\n"
            f"                {entity_name}Model.created_at,\n"
            f"                {entity_name}Model.id_{snake_name},\n"
            "            )\n"
            f"            .limit(limit)\n"
            "        )\n"
            "        result = await self._session.execute(statement)\n"
            f"        return [\n"
            f"            {entity_name}Entity(\n"
            f"            {entity_constructor}\n"
            "            )\n"
            f"            for db_{snake_name} in result.scalars()\n"
            "        ]"
        ),
    )

    documents[dependencies_path] = _insert_after_marker(
        documents[dependencies_path],
        "# gencli:use-case-imports",
        use_case_import,
    )
    documents[dependencies_path] = _insert_after_marker(
        documents[dependencies_path],
        "# gencli:use-case-providers",
        (
            f"def get_list_{plural_name}(\n"
            f"    repository: {entity_name}Repository = Depends(\n"
            f"        get_{snake_name}_repository\n"
            "    ),\n"
            f") -> List{plural_entity}:\n"
            f"    return List{plural_entity}(repository)"
        ),
    )

    documents[main_path] = _insert_after_marker(
        documents[main_path],
        "# gencli:router-imports",
        (
            f"from src.modules.{plural_name}.infrastructure.http.routers "
            f"import router as {plural_name}_router"
        ),
    )
    documents[main_path] = _insert_after_marker(
        documents[main_path],
        "# gencli:router-includes",
        f'    app.include_router({plural_name}_router, prefix="/api/v1")',
    )

    _write_atomically(documents)


def main() -> int:
    if len(sys.argv) != 5:
        print(
            "Uso: register_uc_list.py <use_case_path> <Entity> <snake_name> "
            "<inline_props>",
            file=sys.stderr,
        )
        return 2
    try:
        register_list(
            Path(sys.argv[1]),
            sys.argv[2],
            sys.argv[3],
            sys.argv[4],
        )
    except MutationError as exc:
        print(f"Error al registrar --uc-list: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
