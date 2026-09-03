import ast
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / ".gen_cli" / "scripts" / "register_uc_list.py"


def _write_base_module(project_root: Path) -> Path:
    module_root = project_root / "src" / "modules" / "users"
    files = {
        module_root / "use_cases" / "list_users.py": "class ListUsers:\n    pass\n",
        module_root / "domain" / "repositories.py": (
            "from typing import Protocol\n\n"
            "# gencli:repository-port-imports\n\n"
            "class UserRepository(Protocol):\n"
            "    # gencli:repository-port-methods\n"
        ),
        module_root / "infrastructure" / "persistence" / "repositories.py": (
            "from sqlalchemy.ext.asyncio import AsyncSession\n\n"
            "from src.modules.users.domain.repositories import UserRepository\n\n"
            "# gencli:repository-adapter-imports\n\n"
            "class PostgresUserRepository(UserRepository):\n"
            "    def __init__(self, session: AsyncSession) -> None:\n"
            "        self._session = session\n\n"
            "    # gencli:repository-adapter-methods\n"
        ),
        module_root / "infrastructure" / "http" / "dependencies.py": (
            "from fastapi import Depends\n"
            "from sqlalchemy.ext.asyncio import AsyncSession\n\n"
            "from src.modules.users.domain.repositories import UserRepository\n"
            "from src.shared.infrastructure.persistence.database import "
            "get_db_session\n\n"
            "# gencli:use-case-imports\n\n"
            "def get_user_repository(\n"
            "    session: AsyncSession = Depends(get_db_session),\n"
            ") -> UserRepository:\n"
            "    raise NotImplementedError\n\n"
            "# gencli:use-case-providers\n"
        ),
        module_root
        / "infrastructure"
        / "http"
        / "routers.py": "from fastapi import APIRouter\n\nrouter = APIRouter()\n",
        project_root / "src" / "main.py": (
            "# gencli:router-imports\n\n"
            "def create_app() -> None:\n"
            "    # gencli:router-includes\n"
        ),
    }
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return module_root / "infrastructure" / "http" / "routers.py"


def _run_script(use_case_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(use_case_path),
            "User",
            "user",
            "nombre:str,email:str",
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_register_uc_list_is_idempotent_and_keeps_python_valid(tmp_path: Path) -> None:
    use_case_path = _write_base_module(tmp_path)

    first_run = _run_script(use_case_path)
    assert first_run.returncode == 0, first_run.stderr

    updated_files = sorted((tmp_path / "src").glob("**/*.py"))
    first_contents = {path: path.read_text(encoding="utf-8") for path in updated_files}
    for path, content in first_contents.items():
        ast.parse(content, filename=str(path))

    second_run = _run_script(use_case_path)
    assert second_run.returncode == 0, second_run.stderr
    assert {
        path: path.read_text(encoding="utf-8") for path in updated_files
    } == first_contents

    main = (tmp_path / "src" / "main.py").read_text(encoding="utf-8")
    assert main.count("import router as users_router") == 1
    assert main.count("app.include_router(users_router") == 1


def test_register_uc_list_fails_without_a_required_marker(tmp_path: Path) -> None:
    generated_file = _write_base_module(tmp_path)
    module_root = generated_file.parents[2]
    port_path = module_root / "domain" / "repositories.py"
    original_content = port_path.read_text(encoding="utf-8")
    port_path.write_text(
        original_content.replace("# gencli:repository-port-methods", ""),
        encoding="utf-8",
    )
    broken_content = port_path.read_text(encoding="utf-8")

    result = _run_script(generated_file)

    assert result.returncode == 1
    assert "marcador requerido" in result.stderr
    assert port_path.read_text(encoding="utf-8") == broken_content
