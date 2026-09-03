"""Completa los contratos base despues de generar ``--uc-delete``."""

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
    _read_required,
    _write_atomically,
)


def register_delete(generated_file: Path, entity_name: str, snake_name: str, inline_properties: str) -> None:
    """Register a soft-delete vertical that only operates on active rows."""
    _parse_properties(inline_properties)
    module_root = _find_module_root(generated_file.resolve())
    plural_name = f"{snake_name}s"
    plural_entity = f"{entity_name}s"
    project_root = _find_project_root(module_root)
    port_path = module_root / "domain" / "repositories.py"
    adapter_path = module_root / "infrastructure" / "persistence" / "repositories.py"
    faker_path = module_root / "infrastructure" / "persistence" / "faker_repositories.py"
    dependencies_path = module_root / "infrastructure" / "http" / "dependencies.py"
    router_path = module_root / "infrastructure" / "http" / "routers.py"
    main_path = project_root / "src" / "main.py"
    documents = _read_required((port_path, adapter_path, dependencies_path, router_path, main_path))
    if faker_path.is_file():
        documents[faker_path] = faker_path.read_text(encoding="utf-8")

    exceptions_import = f"from src.modules.{plural_name}.domain.exceptions import {entity_name}NotFoundError"
    model_import = f"from src.modules.{plural_name}.infrastructure.persistence.models import {entity_name}Model"
    documents[port_path] = _insert_after_marker(documents[port_path], "# gencli:repository-port-imports", "from uuid import UUID")
    documents[port_path] = _insert_after_marker(documents[port_path], "# gencli:repository-port-methods", "    async def soft_delete(self, identifier: UUID) -> None:\n        \"\"\"Elimina logicamente una entidad activa sin confirmar la transaccion.\"\"\"\n        ...")
    for addition in ("from datetime import datetime, timezone", "from uuid import UUID", exceptions_import, model_import):
        documents[adapter_path] = _insert_after_marker(documents[adapter_path], "# gencli:repository-adapter-imports", addition)
    documents[adapter_path] = _insert_after_marker(
        documents[adapter_path], "# gencli:repository-adapter-methods",
        f"    async def soft_delete(self, identifier: UUID) -> None:\n        statement = select({entity_name}Model).where(\n            {entity_name}Model.id_{snake_name} == identifier,\n            {entity_name}Model.deleted_at.is_(None),\n        )\n        result = await self._session.execute(statement)\n        model = result.scalar_one_or_none()\n        if model is None:\n            raise {entity_name}NotFoundError(\"{entity_name} not found\")\n        model.deleted_at = datetime.now(timezone.utc)\n        await self._session.flush()",
    )

    # --- Faker adapter ---
    if faker_path in documents:
        documents[faker_path] = _insert_after_marker(
            documents[faker_path],
            "# gencli:faker-repository-imports",
            exceptions_import,
        )
        documents[faker_path] = _insert_after_marker(
            documents[faker_path],
            "# gencli:faker-repository-methods",
            (
                f"    async def soft_delete(self, identifier: UUID) -> None:\n"
                f"        active = self._active()\n"
                f"        if not any(e.id_{snake_name} == identifier for e in active):\n"
                f'            raise {entity_name}NotFoundError("{entity_name} not found")\n'
                f"        self._store.deleted_ids.add(identifier)"
            ),
        )

    use_case_import = f"from src.modules.{plural_name}.use_cases.delete_{plural_name} import Delete{plural_entity}"
    documents[dependencies_path] = _insert_after_marker(documents[dependencies_path], "# gencli:use-case-imports", use_case_import)
    documents[dependencies_path] = _insert_after_marker(documents[dependencies_path], "# gencli:use-case-imports", "from src.shared.domain.unit_of_work import UnitOfWork\nfrom src.shared.infrastructure.http.dependencies import get_unit_of_work")
    documents[dependencies_path] = _insert_after_marker(documents[dependencies_path], "# gencli:use-case-providers", f"def get_delete_{plural_name}(\n    repository: {entity_name}Repository = Depends(get_{snake_name}_repository),\n    unit_of_work: UnitOfWork = Depends(get_unit_of_work),\n) -> Delete{plural_entity}:\n    return Delete{plural_entity}(repository, unit_of_work)")
    documents[router_path] = _insert_after_marker(
        documents[router_path], "# gencli:router-imports", "from uuid import UUID"
    )
    documents[router_path] = _insert_after_marker(documents[router_path], "# gencli:router-imports", f"from .controllers.delete_{plural_name}_controller import delete_{plural_name}_controller\nfrom src.modules.{plural_name}.infrastructure.http.dependencies import get_delete_{plural_name}\nfrom src.modules.{plural_name}.use_cases.delete_{plural_name} import Delete{plural_entity}")
    documents[router_path] = _append_after_marker(documents[router_path], "# gencli:routes", f'@router.delete("/{{identifier}}", status_code=204)\nasync def delete_{plural_name}(\n    identifier: UUID,\n    use_case: Annotated[Delete{plural_entity}, Depends(get_delete_{plural_name})],\n) -> None:\n    await delete_{plural_name}_controller(use_case, identifier)')
    documents[main_path] = _insert_after_marker(documents[main_path], "# gencli:router-imports", f"from src.modules.{plural_name}.infrastructure.http.routers import router as {plural_name}_router")
    documents[main_path] = _insert_after_marker(documents[main_path], "# gencli:router-includes", f'    app.include_router({plural_name}_router, prefix="/api/v1")')
    _write_atomically(documents)


def main() -> int:
    if len(sys.argv) != 5:
        print("Uso: register_uc_delete.py <archivo> <Entity> <snake_name> <inline_props>", file=sys.stderr)
        return 2
    try:
        register_delete(Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4])
    except MutationError as exc:
        print(f"Error al registrar --uc-delete: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
