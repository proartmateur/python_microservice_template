"""Completa los contratos base despues de generar ``--uc-create``."""

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


def register_create(
    generated_file: Path,
    entity_name: str,
    snake_name: str,
    inline_properties: str,
) -> None:
    """Register a transactional create vertical without repository commits."""
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
    exception_import = (
        f"from src.modules.{plural_name}.domain.exceptions import "
        f"{entity_name}AlreadyExistsError"
    )
    model_import = (
        f"from src.modules.{plural_name}.infrastructure.persistence.models import "
        f"{entity_name}Model"
    )
    entity_arguments = ",\n            ".join(
        [f"id_{snake_name}=entity.id_{snake_name}"]
        + [f"{property_name}=entity.{property_name}" for property_name in properties]
        + ["created_at=entity.created_at"]
    )
    response_arguments = ",\n        ".join(
        [f"id=entity.id_{snake_name}"]
        + [f"{property_name}=entity.{property_name}" for property_name in properties]
        + ["created_at=entity.created_at"]
    )

    documents[port_path] = _insert_after_marker(
        documents[port_path], "# gencli:repository-port-imports", entity_import
    )
    documents[port_path] = _insert_after_marker(
        documents[port_path],
        "# gencli:repository-port-methods",
        (
            f"    async def save(self, entity: {entity_name}Entity) -> {entity_name}Entity:\n"
            '        """Guarda una entidad sin confirmar la transaccion."""\n'
            "        ..."
        ),
    )

    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path], "# gencli:repository-adapter-imports", entity_import
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path], "# gencli:repository-adapter-imports", exception_import
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path], "# gencli:repository-adapter-imports", model_import
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path],
        "# gencli:repository-adapter-imports",
        "from sqlalchemy.exc import IntegrityError",
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path],
        "# gencli:repository-adapter-methods",
        (
            f"    async def save(self, entity: {entity_name}Entity) -> {entity_name}Entity:\n"
            f"        model = {entity_name}Model(\n            {entity_arguments}\n        )\n"
            "        self._session.add(model)\n"
            "        try:\n"
            "            await self._session.flush()\n"
            "        except IntegrityError as exc:\n"
            "            await self._session.rollback()\n"
            f'            raise {entity_name}AlreadyExistsError("{entity_name} already exists") from exc\n'
            "        return entity"
        ),
    )

    use_case_import = (
        f"from src.modules.{plural_name}.use_cases.create_{plural_name} import "
        f"Create{plural_entity}"
    )
    documents[dependencies_path] = _insert_after_marker(
        documents[dependencies_path], "# gencli:use-case-imports", use_case_import
    )
    documents[dependencies_path] = _insert_after_marker(
        documents[dependencies_path],
        "# gencli:use-case-imports",
        "from src.shared.domain.unit_of_work import UnitOfWork\n"
        "from src.shared.infrastructure.http.dependencies import get_unit_of_work",
    )
    documents[dependencies_path] = _insert_after_marker(
        documents[dependencies_path],
        "# gencli:use-case-providers",
        (
            f"def get_create_{plural_name}(\n"
            f"    repository: {entity_name}Repository = Depends(get_{snake_name}_repository),\n"
            "    unit_of_work: UnitOfWork = Depends(get_unit_of_work),\n"
            f") -> Create{plural_entity}:\n"
            f"    return Create{plural_entity}(repository, unit_of_work)"
        ),
    )

    documents[schemas_path] = _insert_after_marker(
        documents[schemas_path],
        "# gencli:schema-imports",
        (
            "from datetime import datetime\n"
            "from uuid import UUID\n\n"
            "from pydantic import BaseModel, ConfigDict\n\n"
            f"{entity_import}"
        ),
    )
    documents[schemas_path] = _insert_after_marker(
        documents[schemas_path],
        "# gencli:schema-models",
        (
            f"class {entity_name}CreateRequest(BaseModel):\n"
            "    model_config = ConfigDict(strict=True)\n"
            + "".join(
                f"    {property_name}: {property_types[property_name]}\n"
                for property_name in properties
            )
            + f"\nclass {entity_name}CreateResponse(BaseModel):\n"
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
            f"def to_{snake_name}_create_response(\n"
            f"    entity: {entity_name}Entity,\n"
            f") -> {entity_name}CreateResponse:\n"
            f"    return {entity_name}CreateResponse(\n        {response_arguments}\n    )"
        ),
    )

    documents[router_path] = _insert_after_marker(
        documents[router_path],
        "# gencli:router-imports",
        (
            f"from src.modules.{plural_name}.infrastructure.http.controllers."
            f"create_{plural_name}_controller import create_{plural_name}_controller\n"
            f"from src.modules.{plural_name}.infrastructure.http.dependencies "
            f"import get_create_{plural_name}\n"
            f"from src.modules.{plural_name}.infrastructure.http.schemas import "
            f"{entity_name}CreateRequest, {entity_name}CreateResponse\n"
            f"from src.modules.{plural_name}.use_cases.create_{plural_name} import "
            f"Create{plural_entity}"
        ),
    )
    documents[router_path] = _insert_after_marker(
        documents[router_path],
        "# gencli:routes",
        (
            '@router.post("/", response_model='
            f"{entity_name}CreateResponse, status_code=201)\n"
            f"async def create_{plural_name}(\n"
            f"    request: {entity_name}CreateRequest,\n"
            f"    use_case: Annotated[Create{plural_entity}, Depends(get_create_{plural_name})],\n"
            f") -> {entity_name}CreateResponse:\n"
            f"    return await create_{plural_name}_controller(use_case, request)"
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
            "Uso: register_uc_create.py <archivo> <Entity> <snake_name> <inline_props>",
            file=sys.stderr,
        )
        return 2
    try:
        register_create(Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4])
    except MutationError as exc:
        print(f"Error al registrar --uc-create: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
