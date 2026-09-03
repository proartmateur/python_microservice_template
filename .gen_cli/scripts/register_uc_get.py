"""Completa los contratos base despues de generar ``--uc-get``."""

# Generated source snippets intentionally retain their readable target formatting.
# ruff: noqa: E501

from __future__ import annotations

import sys
from pathlib import Path

from register_uc_list import (
    MutationError,
    _find_module_root,
    _find_project_root,
    _insert_after_marker,
    _parse_properties,
    _parse_property_types,
    _read_required,
    _write_atomically,
)


def _append_after_marker(document: str, marker: str, addition: str) -> str:
    """Append routes so ``/{id}`` cannot shadow static routes generated earlier."""
    if addition in document:
        return document
    if marker not in document:
        raise MutationError(f"No se encontró el marcador requerido: {marker}")
    return f"{document.rstrip()}\n\n{addition}\n"


def register_get(
    generated_file: Path,
    entity_name: str,
    snake_name: str,
    inline_properties: str,
) -> None:
    """Register an individual read vertical that composes with collection routes."""
    properties = _parse_properties(inline_properties)
    property_types = _parse_property_types(inline_properties)
    module_root = _find_module_root(generated_file.resolve())
    plural_name = f"{snake_name}s"
    plural_entity = f"{entity_name}s"
    project_root = _find_project_root(module_root)

    port_path = module_root / "domain" / "repositories.py"
    adapter_path = module_root / "infrastructure" / "persistence" / "repositories.py"
    dependencies_path = module_root / "infrastructure" / "http" / "dependencies.py"
    router_path = module_root / "infrastructure" / "http" / "routers.py"
    schemas_path = module_root / "infrastructure" / "http" / "schemas.py"
    main_path = project_root / "src" / "main.py"
    documents = _read_required(
        (port_path, adapter_path, dependencies_path, router_path, schemas_path, main_path)
    )

    entity_import = (
        f"from src.modules.{plural_name}.domain.entities import {entity_name}Entity"
    )
    model_import = (
        f"from src.modules.{plural_name}.infrastructure.persistence.models import "
        f"{entity_name}Model"
    )
    entity_arguments = ",\n                ".join(
        [f"id_{snake_name}=model.id_{snake_name}"]
        + [f"{property_name}=model.{property_name}" for property_name in properties]
        + ["created_at=model.created_at"]
    )
    response_arguments = ",\n        ".join(
        [f"id=entity.id_{snake_name}"]
        + [f"{property_name}=entity.{property_name}" for property_name in properties]
        + ["created_at=entity.created_at"]
    )

    documents[port_path] = _insert_after_marker(
        documents[port_path], "# gencli:repository-port-imports", "from uuid import UUID"
    )
    documents[port_path] = _insert_after_marker(
        documents[port_path], "# gencli:repository-port-imports", entity_import
    )
    documents[port_path] = _insert_after_marker(
        documents[port_path],
        "# gencli:repository-port-methods",
        (
            f"    async def find_by_id(self, identifier: UUID) -> {entity_name}Entity | None:\n"
            '        """Busca una entidad activa por su identidad."""\n'
            "        ..."
        ),
    )

    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path], "# gencli:repository-adapter-imports", "from uuid import UUID"
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path], "# gencli:repository-adapter-imports", entity_import
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path], "# gencli:repository-adapter-imports", model_import
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path],
        "# gencli:repository-adapter-methods",
        (
            f"    async def find_by_id(self, identifier: UUID) -> {entity_name}Entity | None:\n"
            f"        statement = select({entity_name}Model).where(\n"
            f"            {entity_name}Model.id_{snake_name} == identifier,\n"
            f"            {entity_name}Model.deleted_at.is_(None),\n"
            "        )\n"
            "        result = await self._session.execute(statement)\n"
            "        model = result.scalar_one_or_none()\n"
            "        if model is None:\n"
            "            return None\n"
            f"        return {entity_name}Entity(\n                {entity_arguments}\n        )"
        ),
    )

    use_case_import = (
        f"from src.modules.{plural_name}.use_cases.get_{plural_name} import "
        f"Get{plural_entity}"
    )
    documents[dependencies_path] = _insert_after_marker(
        documents[dependencies_path], "# gencli:use-case-imports", use_case_import
    )
    documents[dependencies_path] = _insert_after_marker(
        documents[dependencies_path],
        "# gencli:use-case-providers",
        (
            f"def get_get_{plural_name}(\n"
            f"    repository: {entity_name}Repository = Depends(get_{snake_name}_repository),\n"
            f") -> Get{plural_entity}:\n"
            f"    return Get{plural_entity}(repository)"
        ),
    )

    documents[schemas_path] = _insert_after_marker(
        documents[schemas_path],
        "# gencli:schema-imports",
        (
            "from datetime import datetime\n"
            "from uuid import UUID\n\n"
            "from pydantic import BaseModel\n\n"
            f"{entity_import}"
        ),
    )
    documents[schemas_path] = _insert_after_marker(
        documents[schemas_path],
        "# gencli:schema-models",
        (
            f"class {entity_name}GetResponse(BaseModel):\n"
            "    id: UUID\n"
            + "".join(
                f"    {property_name}: {property_types[property_name]}\n"
                for property_name in properties
            )
            + "    created_at: datetime"
        ),
    )
    documents[schemas_path] = _insert_after_marker(
        documents[schemas_path],
        "# gencli:schema-mappers",
        (
            f"def to_{snake_name}_get_response(\n"
            f"    entity: {entity_name}Entity,\n"
            f") -> {entity_name}GetResponse:\n"
            f"    return {entity_name}GetResponse(\n        {response_arguments}\n    )"
        ),
    )

    documents[router_path] = _insert_after_marker(
        documents[router_path],
        "# gencli:router-imports",
        (
            "from uuid import UUID\n\n"
            f"from .controllers.get_{plural_name}_controller import "
            f"get_{plural_name}_controller\n"
            f"from src.modules.{plural_name}.infrastructure.http.dependencies "
            f"import get_get_{plural_name}\n"
            f"from src.modules.{plural_name}.infrastructure.http.schemas import "
            f"{entity_name}GetResponse\n"
            f"from src.modules.{plural_name}.use_cases.get_{plural_name} import "
            f"Get{plural_entity}"
        ),
    )
    documents[router_path] = _append_after_marker(
        documents[router_path],
        "# gencli:routes",
        (
            '@router.get("/{identifier}", response_model='
            f"{entity_name}GetResponse)\n"
            f"async def get_{plural_name}(\n"
            "    identifier: UUID,\n"
            f"    use_case: Annotated[Get{plural_entity}, Depends(get_get_{plural_name})],\n"
            f") -> {entity_name}GetResponse:\n"
            f"    return await get_{plural_name}_controller(use_case, identifier)"
        ),
    )
    documents[main_path] = _insert_after_marker(
        documents[main_path],
        "# gencli:router-imports",
        f"from src.modules.{plural_name}.infrastructure.http.routers "
        f"import router as {plural_name}_router",
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
            "Uso: register_uc_get.py <archivo> <Entity> <snake_name> <inline_props>",
            file=sys.stderr,
        )
        return 2
    try:
        register_get(Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4])
    except MutationError as exc:
        print(f"Error al registrar --uc-get: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
