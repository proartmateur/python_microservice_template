import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOMAIN_ROOT = PROJECT_ROOT / "src"

FORBIDDEN_IMPORTS = {"fastapi", "pydantic", "sqlalchemy"}


def _import_roots(source: str) -> set[str]:
    tree = ast.parse(source)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_domain_packages_do_not_import_infrastructure_libraries() -> None:
    domain_files = sorted(DOMAIN_ROOT.glob("**/domain/**/*.py"))
    assert domain_files, "No se encontraron paquetes de dominio para validar."

    violations = {
        path.relative_to(PROJECT_ROOT): _import_roots(path.read_text())
        & FORBIDDEN_IMPORTS
        for path in domain_files
    }
    violations = {path: imports for path, imports in violations.items() if imports}

    assert not violations, f"Imports prohibidos en dominio: {violations}"
