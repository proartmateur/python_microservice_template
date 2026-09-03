"""Completa los contratos base despues de generar ``--uc-update``."""

# Generated source snippets intentionally retain their readable target formatting.
# ruff: noqa: E501

from __future__ import annotations

import sys
from pathlib import Path

from register_uc_get import _append_after_marker
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


def register_update(
    generated_file: Path,
    entity_name: str,
    snake_name: str,
    inline_properties: str,
) -> None:
    """Register a PUT vertical with typed persistence failures."""
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

    entity_import = f"from src.modules.{plural_name}.domain.entities import {entity_name}Entity"
    exceptions_import = (
        f"from src.modules.{plural_name}.domain.exceptions import {entity_name}AlreadyExistsError, {entity_name}NotFoundError"
    )
    model_import = f"from src.modules.{plural_name}.infrastructure.persistence.models import {entity_name}Model"
    entity_arguments = ",\n                ".join(
        [f"id_{snake_name}=model.id_{snake_name}"]
        + [f"{property}=model.{property}" for property in properties]
        + ["created_at=model.created_at"]
    )
    response_arguments = ",\n        ".join(
        [f"id=entity.id_{snake_name}"]
        + [f"{property}=entity.{property}" for property in properties]
        + ["created_at=entity.created_at"]
    )

    documents[port_path] = _insert_after_marker(
        documents[port_path], "# gencli:repository-port-imports", "from uuid import UUID"
    )
    documents[port_path] = _insert_after_marker(
        documents[port_path], "# gencli:repository-port-imports", entity_import
    )
    documents[port_path] = _insert_after_marker(
        documents[port_path], "# gencli:repository-port-methods",
        f"    async def update(self, identifier: UUID, **values: object) -> {entity_name}Entity:\n        \"\"\"Actualiza una entidad activa sin confirmar la transaccion.\"\"\"\n        ...",
    )

    for addition in ("from uuid import UUID", "from typing import cast", entity_import, exceptions_import, model_import, "from sqlalchemy.exc import IntegrityError"):
        documents[adapter_path] = _insert_after_marker(
            documents[adapter_path], "# gencli:repository-adapter-imports", addition
        )
    assignments = "\n        ".join(
        f"model.{property} = cast({property_types[property]!r}, values[{property!r}])"
        for property in properties
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path], "# gencli:repository-adapter-methods",
        (
            f"    async def update(self, identifier: UUID, **values: object) -> {entity_name}Entity:\n"
            f"        statement = select({entity_name}Model).where(\n            {entity_name}Model.id_{snake_name} == identifier,\n            {entity_name}Model.deleted_at.is_(None),\n        )\n"
            "        result = await self._session.execute(statement)\n"
            "        model = result.scalar_one_or_none()\n"
            "        if model is None:\n"
            f"            raise {entity_name}NotFoundError(\"{entity_name} not found\")\n"
            f"        {assignments}\n"
            "        try:\n            await self._session.flush()\n"
            "        except IntegrityError as exc:\n"
            f"            raise {entity_name}AlreadyExistsError(\"{entity_name} already exists\") from exc\n"
            f"        return {entity_name}Entity(\n                {entity_arguments}\n        )"
        ),
    )

    use_case_import = f"from src.modules.{plural_name}.use_cases.update_{plural_name} import Update{plural_entity}"
    documents[dependencies_path] = _insert_after_marker(documents[dependencies_path], "# gencli:use-case-imports", use_case_import)
    documents[dependencies_path] = _insert_after_marker(
        documents[dependencies_path], "# gencli:use-case-imports",
        "from src.shared.domain.unit_of_work import UnitOfWork\nfrom src.shared.infrastructure.http.dependencies import get_unit_of_work",
    )
    documents[dependencies_path] = _insert_after_marker(
        documents[dependencies_path], "# gencli:use-case-providers",
        f"def get_update_{plural_name}(\n    repository: {entity_name}Repository = Depends(get_{snake_name}_repository),\n    unit_of_work: UnitOfWork = Depends(get_unit_of_work),\n) -> Update{plural_entity}:\n    return Update{plural_entity}(repository, unit_of_work)",
    )

    # Import normalization merges overlapping generated imports after the first run.
    # The model class is a stable sentinel that prevents reinserting that block.
    if f"class {entity_name}UpdateRequest" not in documents[schemas_path]:
        documents[schemas_path] = _insert_after_marker(
            documents[schemas_path], "# gencli:schema-imports",
            f"from datetime import datetime\nfrom uuid import UUID\n\nfrom pydantic import BaseModel, ConfigDict\n\n{entity_import}",
        )
    documents[schemas_path] = _insert_after_marker(
        documents[schemas_path], "# gencli:schema-models",
        f"class {entity_name}UpdateRequest(BaseModel):\n    model_config = ConfigDict(strict=True)\n" + "".join(f"    {property}: {property_types[property]}\n" for property in properties) + f"\nclass {entity_name}UpdateResponse(BaseModel):\n    id: UUID\n" + "".join(f"    {property}: {property_types[property]}\n" for property in properties) + "    created_at: datetime",
    )
    documents[schemas_path] = _insert_after_marker(
        documents[schemas_path], "# gencli:schema-mappers",
        f"def to_{snake_name}_update_response(entity: {entity_name}Entity) -> {entity_name}UpdateResponse:\n    return {entity_name}UpdateResponse(\n        {response_arguments}\n    )",
    )

    documents[router_path] = _insert_after_marker(
        documents[router_path], "# gencli:router-imports", "from uuid import UUID"
    )
    documents[router_path] = _insert_after_marker(
        documents[router_path], "# gencli:router-imports",
        f"from .controllers.update_{plural_name}_controller import update_{plural_name}_controller\nfrom src.modules.{plural_name}.infrastructure.http.dependencies import get_update_{plural_name}\nfrom src.modules.{plural_name}.infrastructure.http.schemas import {entity_name}UpdateRequest, {entity_name}UpdateResponse\nfrom src.modules.{plural_name}.use_cases.update_{plural_name} import Update{plural_entity}",
    )
    documents[router_path] = _append_after_marker(
        documents[router_path], "# gencli:routes",
        f'@router.put("/{{identifier}}", response_model={entity_name}UpdateResponse)\nasync def update_{plural_name}(\n    identifier: UUID,\n    request: {entity_name}UpdateRequest,\n    use_case: Annotated[Update{plural_entity}, Depends(get_update_{plural_name})],\n) -> {entity_name}UpdateResponse:\n    return await update_{plural_name}_controller(use_case, identifier, request)',
    )
    documents[main_path] = _insert_after_marker(documents[main_path], "# gencli:router-imports", f"from src.modules.{plural_name}.infrastructure.http.routers import router as {plural_name}_router")
    documents[main_path] = _insert_after_marker(documents[main_path], "# gencli:router-includes", f'    app.include_router({plural_name}_router, prefix="/api/v1")')
    _write_atomically(documents)


def main() -> int:
    if len(sys.argv) != 5:
        print("Uso: register_uc_update.py <archivo> <Entity> <snake_name> <inline_props>", file=sys.stderr)
        return 2
    try:
        register_update(Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4])
    except MutationError as exc:
        print(f"Error al registrar --uc-update: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
