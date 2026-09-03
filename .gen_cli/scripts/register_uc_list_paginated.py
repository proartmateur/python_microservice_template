"""Completa los contratos base después de generar ``--uc-list-paginated``."""

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


def register_list_paginated(
    generated_file: Path,
    entity_name: str,
    snake_name: str,
    inline_properties: str,
) -> None:
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
        (
            port_path,
            adapter_path,
            dependencies_path,
            router_path,
            schemas_path,
            main_path,
        )
    )

    entity_import = (
        f"from src.modules.{plural_name}.domain.entities import {entity_name}Entity"
    )
    model_import = (
        f"from src.modules.{plural_name}.infrastructure.persistence.models import "
        f"{entity_name}Model"
    )
    pagination_import = (
        "from src.shared.domain.pagination import CursorPage, KeysetCursor"
    )
    entity_constructor = ",\n                ".join(
        [f"id_{snake_name}=db_{snake_name}.id_{snake_name}"]
        + [
            f"{property_name}=db_{snake_name}.{property_name}"
            for property_name in properties
        ]
        + [f"created_at=db_{snake_name}.created_at"]
    )

    documents[port_path] = _insert_after_marker(
        documents[port_path], "# gencli:repository-port-imports", entity_import
    )
    documents[port_path] = _insert_after_marker(
        documents[port_path], "# gencli:repository-port-imports", pagination_import
    )
    documents[port_path] = _insert_after_marker(
        documents[port_path],
        "# gencli:repository-port-methods",
        (
            f"    async def list_paginated(\n"
            "        self, *, limit: int, cursor: KeysetCursor | None\n"
            f"    ) -> CursorPage[{entity_name}Entity]:\n"
            '        """Devuelve una página keyset de entidades activas."""\n'
            "        ..."
        ),
    )

    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path],
        "# gencli:repository-adapter-imports",
        entity_import,
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path],
        "# gencli:repository-adapter-imports",
        model_import,
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path],
        "# gencli:repository-adapter-imports",
        pagination_import,
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path],
        "# gencli:repository-adapter-methods",
        (
            f"    async def list_paginated(\n"
            "        self, *, limit: int, cursor: KeysetCursor | None\n"
            f"    ) -> CursorPage[{entity_name}Entity]:\n"
            f"        statement = select({entity_name}Model).where(\n"
            f"            {entity_name}Model.deleted_at.is_(None)\n"
            "        )\n"
            "        if cursor is not None:\n"
            "            statement = statement.where(\n"
            "                or_(\n"
            f"                    {entity_name}Model.created_at > cursor.created_at,\n"
            "                    and_(\n"
            f"                        {entity_name}Model.created_at\n"
            "                        == cursor.created_at,\n"
            f"                        {entity_name}Model.id_{snake_name}\n"
            "                        > cursor.identifier,\n"
            "                    ),\n"
            "                )\n"
            "            )\n"
            "        statement = (\n"
            "            statement.order_by(\n"
            f"                {entity_name}Model.created_at,\n"
            f"                {entity_name}Model.id_{snake_name},\n"
            "            )\n"
            "            .limit(limit + 1)\n"
            "        )\n"
            "        result = await self._session.execute(statement)\n"
            f"        rows = list(result.scalars())\n"
            "        has_next = len(rows) > limit\n"
            "        page_rows = rows[:limit]\n"
            "        next_position = None\n"
            "        if has_next:\n"
            "            last_row = page_rows[-1]\n"
            "            next_position = KeysetCursor(\n"
            "                created_at=last_row.created_at,\n"
            f"                identifier=last_row.id_{snake_name},\n"
            "            )\n"
            "        return CursorPage(\n"
            "            items=[\n"
            f"                {entity_name}Entity(\n"
            f"                {entity_constructor}\n"
            "                )\n"
            f"                for db_{snake_name} in page_rows\n"
            "            ],\n"
            "            next_position=next_position,\n"
            "            has_next=has_next,\n"
            "        )"
        ),
    )

    use_case_import = (
        f"from src.modules.{plural_name}.use_cases.list_paginated_{plural_name} "
        f"import ListPaginated{plural_entity}"
    )
    documents[dependencies_path] = _insert_after_marker(
        documents[dependencies_path], "# gencli:use-case-imports", use_case_import
    )
    documents[dependencies_path] = _insert_after_marker(
        documents[dependencies_path],
        "# gencli:use-case-imports",
        "from src.shared.domain.pagination import CursorCodec\n"
        "from src.shared.infrastructure.http.dependencies import get_cursor_codec",
    )
    documents[dependencies_path] = _insert_after_marker(
        documents[dependencies_path],
        "# gencli:use-case-providers",
        (
            f"def get_list_paginated_{plural_name}(\n"
            f"    repository: {entity_name}Repository = Depends(\n"
            f"        get_{snake_name}_repository\n"
            "    ),\n"
            "    cursor_codec: CursorCodec = Depends(get_cursor_codec),\n"
            f") -> ListPaginated{plural_entity}:\n"
            f"    return ListPaginated{plural_entity}(repository, cursor_codec)"
        ),
    )

    item_response = f"{entity_name}PaginatedItemResponse"
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
            f"class {item_response}(BaseModel):\n"
            "    id: UUID\n"
            + "".join(
                f"    {property_name}: {property_types[property_name]}\n"
                for property_name in properties
            )
            + "    created_at: datetime\n\n"
            f"class {entity_name}PaginatedResponse(BaseModel):\n"
            f"    items: list[{item_response}]\n"
            "    next_cursor: str | None\n"
            "    has_next: bool\n"
            "    limit: int"
        ),
    )
    response_arguments = ",\n        ".join(
        [f"id=entity.id_{snake_name}"]
        + [f"{property_name}=entity.{property_name}" for property_name in properties]
        + ["created_at=entity.created_at"]
    )
    documents[schemas_path] = _insert_after_marker(
        documents[schemas_path],
        "# gencli:schema-mappers",
        (
            f"def to_{snake_name}_paginated_item_response(\n"
            f"    entity: {entity_name}Entity,\n"
            f") -> {item_response}:\n"
            f"    return {item_response}(\n"
            f"        {response_arguments}\n"
            "    )"
        ),
    )

    documents[router_path] = _insert_after_marker(
        documents[router_path],
        "# gencli:router-imports",
        (
            f"from .controllers.list_paginated_{plural_name}_controller import "
            f"list_paginated_{plural_name}_controller\n"
            f"from src.modules.{plural_name}.infrastructure.http.dependencies "
            f"import get_list_paginated_{plural_name}\n"
            f"from src.modules.{plural_name}.infrastructure.http.schemas "
            f"import {entity_name}PaginatedResponse\n"
            f"from src.modules.{plural_name}.use_cases.list_paginated_{plural_name} "
            f"import ListPaginated{plural_entity}"
        ),
    )
    documents[router_path] = _insert_after_marker(
        documents[router_path],
        "# gencli:routes",
        (
            "@router.get(\n"
            '    "/paginated",\n'
            f"    response_model={entity_name}PaginatedResponse,\n"
            ")\n"
            f"async def list_paginated_{plural_name}(\n"
            f"    use_case: Annotated[\n"
            f"        ListPaginated{plural_entity},\n"
            f"        Depends(get_list_paginated_{plural_name}),\n"
            "    ],\n"
            "    limit: Annotated[int, Query(ge=1, le=100)] = 50,\n"
            "    cursor: str | None = None,\n"
            f") -> {entity_name}PaginatedResponse:\n"
            f"    return await list_paginated_{plural_name}_controller(\n"
            "        use_case, limit=limit, cursor=cursor\n"
            "    )"
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
            "Uso: register_uc_list_paginated.py <archivo> <Entity> <snake_name> "
            "<inline_props>",
            file=sys.stderr,
        )
        return 2
    try:
        register_list_paginated(
            Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
        )
    except MutationError as exc:
        print(f"Error al registrar --uc-list-paginated: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
