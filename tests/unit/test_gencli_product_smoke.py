import ast
from difflib import unified_diff
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCT_PROPERTIES = "name:str,user:UUID,is_physical:bool"
USE_CASE_OPTIONS = (
    "--uc-list",
    "--uc-list-paginated",
    "--uc-find-by",
    "--uc-create",
    "--uc-get",
    "--uc-update",
    "--uc-delete",
)


def _prepare_isolated_project(project_root: Path) -> None:
    shutil.copy2(PROJECT_ROOT / "gen", project_root / "gen")
    shutil.copy2(PROJECT_ROOT / "gen_config.json", project_root / "gen_config.json")
    shutil.copy2(PROJECT_ROOT / "arq.json", project_root / "arq.json")
    shutil.copytree(
        PROJECT_ROOT / ".gen_cli" / "scripts",
        project_root / ".gen_cli" / "scripts",
    )

    main_path = project_root / "src" / "main.py"
    main_path.parent.mkdir(parents=True)
    main_path.write_text(
        "# gencli:router-imports\n\n"
        "def create_app() -> None:\n"
        "    # gencli:router-includes\n",
        encoding="utf-8",
    )


def _run_gen(project_root: Path, option: str) -> None:
    result = subprocess.run(
        ["./gen", option, "Product", PRODUCT_PROPERTIES],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_gencli_product_incremental_smoke_is_typed_and_idempotent(
    tmp_path: Path,
) -> None:
    _prepare_isolated_project(tmp_path)

    _run_gen(tmp_path, "--hex")
    for option in USE_CASE_OPTIONS:
        _run_gen(tmp_path, option)

    generated_sources = sorted((tmp_path / "src").glob("**/*.py"))
    first_contents = {
        path.relative_to(tmp_path): path.read_text(encoding="utf-8")
        for path in generated_sources
    }
    for path, content in first_contents.items():
        ast.parse(content, filename=str(path))

    for option in USE_CASE_OPTIONS:
        _run_gen(tmp_path, option)
    second_contents = {
        path.relative_to(tmp_path): path.read_text(encoding="utf-8")
        for path in generated_sources
    }
    changed_files = [
        path
        for path, content in second_contents.items()
        if content != first_contents[path]
    ]
    assert not changed_files, "\n".join(
        "\n".join(
            unified_diff(
                first_contents[path].splitlines(),
                second_contents[path].splitlines(),
                fromfile=f"first/{path}",
                tofile=f"second/{path}",
            )
        )
        for path in changed_files
    )

    module_root = tmp_path / "src" / "modules" / "products"
    entities = (module_root / "domain" / "entities.py").read_text(encoding="utf-8")
    models = (
        module_root / "infrastructure" / "persistence" / "models.py"
    ).read_text(encoding="utf-8")
    schemas = (
        module_root / "infrastructure" / "http" / "schemas.py"
    ).read_text(encoding="utf-8")
    repositories = (
        module_root / "infrastructure" / "persistence" / "repositories.py"
    ).read_text(encoding="utf-8")
    router = (
        module_root / "infrastructure" / "http" / "routers.py"
    ).read_text(encoding="utf-8")

    assert "user: UUID" in entities
    assert "is_physical: bool" in entities
    assert "user: Mapped[UUID]" in models
    assert "is_physical: Mapped[bool]" in models
    assert schemas.count("user: UUID") == 8
    assert schemas.count("is_physical: bool") == 8
    assert "isPhisical" not in "\n".join(first_contents.values())
    assert '"user": ProductModel.user' in repositories
    assert '"is_physical": ProductModel.is_physical' in repositories
    assert ".offset(" not in repositories
    assert repositories.count("ProductModel.deleted_at.is_(None)") == 6
    for endpoint in (
        "async def list_products(",
        "async def list_paginated_products(",
        "async def find_by_products(",
        "async def create_products(",
        "async def get_products(",
        "async def update_products(",
        "async def delete_products(",
    ):
        assert endpoint in router
    assert router.index('"/paginated"') < router.index('"/{identifier}"')
    assert router.index('"/find-by"') < router.index('"/{identifier}"')
