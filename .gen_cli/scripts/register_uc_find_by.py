"""Completa los contratos base después de generar ``--uc-find-by``."""

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


def register_find_by(
    generated_file: Path,
    entity_name: str,
    snake_name: str,
    inline_properties: str,
) -> None:
    """Register a bounded/keyset find-by vertical without dynamic SQL."""
    properties = _parse_properties(inline_properties)
    property_types = _parse_property_types(inline_properties)
    module_root = _find_module_root(generated_file.resolve())
    plural_name = f"{snake_name}s"
    plural_entity = f"{entity_name}s"
    project_root = _find_project_root(module_root)

    port_path = module_root / "domain" / "repositories.py"
    adapter_path = module_root / "infrastructure" / "persistence" / "repositories.py"
    faker_path = module_root / "infrastructure" / "persistence" / "faker_repositories.py"
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
    if faker_path.is_file():
        documents[faker_path] = faker_path.read_text(encoding="utf-8")

    entity_import = (
        f"from src.modules.{plural_name}.domain.entities import {entity_name}Entity"
    )
    model_import = (
        f"from src.modules.{plural_name}.infrastructure.persistence.models import "
        f"{entity_name}Model"
    )
    find_by_import = (
        "from src.shared.domain.find_by import FindByCriteria, FindByOperator, "
        "FindByResult"
    )
    port_find_by_import = (
        "from src.shared.domain.find_by import FindByCriteria, FindByResult"
    )
    pagination_import = "from src.shared.domain.pagination import KeysetCursor"
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
        documents[port_path],
        "# gencli:repository-port-imports",
        port_find_by_import,
    )
    documents[port_path] = _insert_after_marker(
        documents[port_path], "# gencli:repository-port-imports", pagination_import
    )
    documents[port_path] = _insert_after_marker(
        documents[port_path],
        "# gencli:repository-port-methods",
        (
            "    async def find_by(\n"
            "        self, *, criteria: FindByCriteria, limit: int,\n"
            "        cursor: KeysetCursor | None, pagination: bool\n"
            f"    ) -> FindByResult[{entity_name}Entity]:\n"
            '        """Busca entidades activas usando un criterio validado."""\n'
            "        ..."
        ),
    )

    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path], "# gencli:repository-adapter-imports", entity_import
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path], "# gencli:repository-adapter-imports", model_import
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path], "# gencli:repository-adapter-imports", find_by_import
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path],
        "# gencli:repository-adapter-imports",
        pagination_import,
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path],
        "# gencli:repository-adapter-imports",
        "from sqlalchemy import and_, or_",
    )
    column_map = ",\n            ".join(
        f'"{property_name}": {entity_name}Model.{property_name}'
        for property_name in properties
    )
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path],
        "# gencli:repository-adapter-methods",
        (
            "    async def find_by(\n"
            "        self, *, criteria: FindByCriteria, limit: int,\n"
            "        cursor: KeysetCursor | None, pagination: bool\n"
            f"    ) -> FindByResult[{entity_name}Entity]:\n"
            "        columns = {\n            " + column_map + "\n        }\n"
            "        column = columns[criteria.field]\n"
            "        if criteria.operator is FindByOperator.EQUALS:\n"
            "            predicate = column == criteria.value\n"
            "        elif criteria.operator is FindByOperator.CONTAINS:\n"
            "            predicate = column.contains(criteria.value)\n"
            "        else:\n"
            "            predicate = column.startswith(criteria.value)\n"
            f"        statement = select({entity_name}Model).where(\n"
            f"            {entity_name}Model.deleted_at.is_(None), predicate\n"
            "        )\n"
            "        if pagination and cursor is not None:\n"
            "            statement = statement.where(\n"
            "                or_(\n"
            f"                    {entity_name}Model.created_at > cursor.created_at,\n"
            "                    and_(\n"
            f"                        {entity_name}Model.created_at == cursor.created_at,\n"
            f"                        {entity_name}Model.id_{snake_name} > cursor.identifier,\n"
            "                    ),\n"
            "                ),\n"
            "            )\n"
            "        statement = statement.order_by(\n"
            f"            {entity_name}Model.created_at, {entity_name}Model.id_{snake_name}\n"
            "        ).limit(limit + 1 if pagination else limit)\n"
            "        result = await self._session.execute(statement)\n"
            "        rows = list(result.scalars())\n"
            "        has_next = pagination and len(rows) > limit\n"
            "        page_rows = rows[:limit]\n"
            "        next_position = None\n"
            "        if has_next:\n"
            "            last_row = page_rows[-1]\n"
            "            next_position = KeysetCursor(\n"
            "                created_at=last_row.created_at,\n"
            f"                identifier=last_row.id_{snake_name},\n"
            "            )\n"
            "        return FindByResult(\n"
            "            items=[\n"
            f"                {entity_name}Entity(\n                {entity_constructor}\n                )\n"
            f"                for db_{snake_name} in page_rows\n"
            "            ],\n"
            "            next_position=next_position,\n"
            "            has_next=has_next,\n"
            "        )"
        ),
    )

    # --- Faker adapter ---
    if faker_path in documents:
        faker_entity_constructor = ",\n                ".join(
            [f"id_{snake_name}=item.id_{snake_name}"]
            + [f"{p}=item.{p}" for p in properties]
            + ["created_at=item.created_at"]
        )
        documents[faker_path] = _insert_after_marker(
            documents[faker_path],
            "# gencli:faker-repository-imports",
            find_by_import,
        )
        documents[faker_path] = _insert_after_marker(
            documents[faker_path],
            "# gencli:faker-repository-imports",
            pagination_import,
        )
        documents[faker_path] = _insert_after_marker(
            documents[faker_path],
            "# gencli:faker-repository-methods",
            (
                "    async def find_by(\n"
                "        self, *, criteria: FindByCriteria, limit: int,\n"
                "        cursor: KeysetCursor | None, pagination: bool\n"
                f"    ) -> FindByResult[{entity_name}Entity]:\n"
                f"        active = sorted(\n"
                f"            self._active(),\n"
                f"            key=lambda e: (e.created_at, e.id_{snake_name}),\n"
                f"        )\n"
                f"        def _match(e: {entity_name}Entity) -> bool:\n"
                f"            val = getattr(e, criteria.field, None)\n"
                f"            if criteria.operator is FindByOperator.EQUALS:\n"
                f"                return val == criteria.value\n"
                f"            if criteria.operator is FindByOperator.CONTAINS:\n"
                f"                return criteria.value in val\n"
                f"            return str(val).startswith(str(criteria.value))\n"
                f"        filtered = [e for e in active if _match(e)]\n"
                f"        if pagination and cursor is not None:\n"
                f"            filtered = [\n"
                f"                e for e in filtered\n"
                f"                if (e.created_at, e.id_{snake_name}) > (cursor.created_at, cursor.identifier)\n"
                f"            ]\n"
                f"        take = limit + 1 if pagination else limit\n"
                f"        page_rows = filtered[:take]\n"
                f"        has_next = pagination and len(filtered) > take\n"
                f"        next_position = None\n"
                f"        if has_next:\n"
                f"            last = page_rows[-1]\n"
                f"            next_position = KeysetCursor(\n"
                f"                created_at=last.created_at,\n"
                f"                identifier=last.id_{snake_name},\n"
                f"            )\n"
                f"        return FindByResult(\n"
                f"            items=[\n"
                f"                {entity_name}Entity(\n                {faker_entity_constructor}\n                )\n"
                f"                for item in page_rows[:limit]\n"
                f"            ],\n"
                f"            next_position=next_position,\n"
                f"            has_next=has_next,\n"
                f"        )"
            ),
        )

    use_case_import = (
        f"from src.modules.{plural_name}.use_cases.find_by_{plural_name} import "
        f"FindBy{plural_entity}"
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
            f"def get_find_by_{plural_name}(\n"
            f"    repository: {entity_name}Repository = Depends(get_{snake_name}_repository),\n"
            "    cursor_codec: CursorCodec = Depends(get_cursor_codec),\n"
            f") -> FindBy{plural_entity}:\n"
            f"    return FindBy{plural_entity}(repository, cursor_codec)"
        ),
    )

    type_map = ",\n        ".join(
        f'"{property_name}": {property_types[property_name]}'
        for property_name in properties
    )
    response_arguments = ",\n        ".join(
        [f"id=entity.id_{snake_name}"]
        + [f"{property_name}=entity.{property_name}" for property_name in properties]
        + ["created_at=entity.created_at"]
    )
    documents[schemas_path] = _insert_after_marker(
        documents[schemas_path],
        "# gencli:schema-imports",
        (
            "from datetime import datetime\n"
            "from typing import ClassVar\n"
            "from uuid import UUID\n\n"
            "from pydantic import BaseModel, ConfigDict, model_validator\n\n"
            f"{entity_import}\n"
            "from src.shared.domain.find_by import FindByCriteria, FindByOperator"
        ),
    )
    documents[schemas_path] = _insert_after_marker(
        documents[schemas_path],
        "# gencli:schema-models",
        (
            f"class {entity_name}FindByQuery(BaseModel):\n"
            "    operator: FindByOperator\n"
            "    value: object\n\n"
            f"class {entity_name}FindByRequest(BaseModel):\n"
            "    model_config = ConfigDict(strict=True)\n"
            "    field: str\n"
            f"    query: {entity_name}FindByQuery\n"
            "    pagination: bool = False\n"
            "    limit: int = 50\n"
            "    cursor: str | None = None\n"
            "    _field_types: ClassVar[dict[str, type[object]]] = {\n        "
            + type_map
            + "\n    }\n\n"
            '    @model_validator(mode="after")\n'
            f'    def validate_find_by(self) -> "{entity_name}FindByRequest":\n'
            "        expected_type = self._field_types.get(self.field)\n"
            "        if expected_type is None:\n"
            '            raise ValueError("field is not searchable")\n'
            "        if type(self.query.value) is not expected_type:\n"
            '            raise ValueError("query.value has an invalid type for field")\n'
            "        is_text_operator = (\n"
            "            self.query.operator is not FindByOperator.EQUALS\n"
            "        )\n"
            "        if is_text_operator and expected_type is not str:\n"
            '            raise ValueError("operator requires a string field")\n'
            "        if not 1 <= self.limit <= 100:\n"
            '            raise ValueError("limit must be between 1 and 100")\n'
            "        if not self.pagination and self.cursor is not None:\n"
            '            raise ValueError("cursor requires pagination=true")\n'
            "        return self\n\n"
            "    def to_criteria(self) -> FindByCriteria:\n"
            "        return FindByCriteria(\n"
            "            field=self.field, operator=self.query.operator, value=self.query.value\n"
            "        )\n\n"
            f"class {entity_name}FindByItemResponse(BaseModel):\n"
            "    id: UUID\n"
            + "".join(
                f"    {property_name}: {property_types[property_name]}\n"
                for property_name in properties
            )
            + "    created_at: datetime\n\n"
            f"class {entity_name}FindByResponse(BaseModel):\n"
            f"    items: list[{entity_name}FindByItemResponse]\n"
            "    next_cursor: str | None\n"
            "    has_next: bool\n"
            "    limit: int"
        ),
    )
    documents[schemas_path] = _insert_after_marker(
        documents[schemas_path],
        "# gencli:schema-mappers",
        (
            f"def to_{snake_name}_find_by_item_response(\n"
            f"    entity: {entity_name}Entity,\n"
            f") -> {entity_name}FindByItemResponse:\n"
            f"    return {entity_name}FindByItemResponse(\n        {response_arguments}\n    )"
        ),
    )

    documents[router_path] = _insert_after_marker(
        documents[router_path],
        "# gencli:router-imports",
        (
            f"from .controllers.find_by_{plural_name}_controller import "
            f"find_by_{plural_name}_controller\n"
            f"from src.modules.{plural_name}.infrastructure.http.dependencies "
            f"import get_find_by_{plural_name}\n"
            f"from src.modules.{plural_name}.infrastructure.http.schemas import "
            f"{entity_name}FindByRequest, {entity_name}FindByResponse\n"
            f"from src.modules.{plural_name}.use_cases.find_by_{plural_name} import "
            f"FindBy{plural_entity}"
        ),
    )
    documents[router_path] = _insert_after_marker(
        documents[router_path],
        "# gencli:routes",
        (
            '@router.post("/find-by", response_model='
            f"{entity_name}FindByResponse)\n"
            f"async def find_by_{plural_name}(\n"
            "    request: " + f"{entity_name}FindByRequest,\n"
            "    use_case: Annotated["
            f"FindBy{plural_entity}, Depends(get_find_by_{plural_name})],\n"
            f") -> {entity_name}FindByResponse:\n"
            f"    return await find_by_{plural_name}_controller(use_case, request)"
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
            "Uso: register_uc_find_by.py <archivo> <Entity> <snake_name> <inline_props>",
            file=sys.stderr,
        )
        return 2
    try:
        register_find_by(Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4])
    except MutationError as exc:
        print(f"Error al registrar --uc-find-by: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
