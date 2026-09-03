import ast
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / ".gen_cli" / "scripts" / "delete_module.py"

MAIN_CONTENT = (
    "from fastapi import FastAPI\n"
    "\n"
    "# gencli:router-imports\n"
    "from src.modules.users.infrastructure.http.routers "
    "import router as users_router\n"
    "from src.modules.orders.infrastructure.http.routers "
    "import router as orders_router\n"
    "\n"
    "\n"
    "def create_app() -> FastAPI:\n"
    "    app = FastAPI()\n"
    "    # gencli:router-includes\n"
    '    app.include_router(users_router, prefix="/api/v1")\n'
    '    app.include_router(orders_router, prefix="/api/v1")\n'
    "    return app\n"
)


def _write_project(project_root: Path) -> None:
    (project_root / "src" / "main.py").parent.mkdir(parents=True)
    (project_root / "src" / "main.py").write_text(MAIN_CONTENT, encoding="utf-8")

    for module in ("users", "orders"):
        module_dir = project_root / "src" / "modules" / module / "domain"
        module_dir.mkdir(parents=True)
        (module_dir / "entities.py").write_text(
            f"class {module.title()}Entity:\n    pass\n", encoding="utf-8"
        )
        tests_dir = project_root / "tests" / "unit" / "modules" / module
        tests_dir.mkdir(parents=True)
        (tests_dir / f"test_{module}.py").write_text(
            "def test_placeholder() -> None:\n    pass\n", encoding="utf-8"
        )


def _run_script(
    project_root: Path, module: str, *extra_args: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), module, *extra_args],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )


def test_delete_module_removes_module_and_cleans_main(tmp_path: Path) -> None:
    _write_project(tmp_path)

    result = _run_script(tmp_path, "User")

    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "src" / "modules" / "users").exists()
    assert not (tmp_path / "tests" / "unit" / "modules" / "users").exists()
    assert (tmp_path / "src" / "modules" / "orders").is_dir()

    main_content = (tmp_path / "src" / "main.py").read_text(encoding="utf-8")
    ast.parse(main_content)
    assert "users_router" not in main_content
    assert "src.modules.users" not in main_content
    assert "orders_router" in main_content
    assert main_content.count("include_router") == 1


def test_delete_module_fails_clearly_when_module_is_missing(tmp_path: Path) -> None:
    _write_project(tmp_path)

    assert _run_script(tmp_path, "users").returncode == 0
    main_after_delete = (tmp_path / "src" / "main.py").read_text(encoding="utf-8")

    second_run = _run_script(tmp_path, "users")

    assert second_run.returncode == 1
    assert "No existe el módulo" in second_run.stderr
    assert (tmp_path / "src" / "main.py").read_text(
        encoding="utf-8"
    ) == main_after_delete


def test_delete_module_dry_run_changes_nothing(tmp_path: Path) -> None:
    _write_project(tmp_path)

    result = _run_script(tmp_path, "users", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "[dry-run]" in result.stdout
    assert (tmp_path / "src" / "modules" / "users").is_dir()
    assert (tmp_path / "src" / "main.py").read_text(encoding="utf-8") == MAIN_CONTENT


def test_delete_module_rejects_invalid_names(tmp_path: Path) -> None:
    _write_project(tmp_path)

    result = _run_script(tmp_path, "../users")

    assert result.returncode == 1
    assert "inválido" in result.stderr
