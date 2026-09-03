"""Reglas de arquitectura que protegen la política de persistencia y errores."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"


def test_persistence_adapters_never_commit() -> None:
    adapters = sorted(SRC_ROOT.glob("modules/*/infrastructure/persistence/*.py"))
    assert adapters, "No se encontraron adaptadores de persistencia para validar."

    offenders = {
        path.relative_to(PROJECT_ROOT): path.read_text(encoding="utf-8").count(
            "commit("
        )
        for path in adapters
        if "commit(" in path.read_text(encoding="utf-8")
    }

    assert not offenders, (
        "El commit vive en el Unit of Work del caso de uso, nunca en el "
        f"adaptador de persistencia: {offenders}"
    )


def test_source_never_matches_error_messages_by_string() -> None:
    sources = sorted(SRC_ROOT.glob("**/*.py"))
    assert sources, "No se encontró código fuente para validar."

    offenders = {
        path.relative_to(PROJECT_ROOT): line_number
        for path in sources
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if "in message" in line
    }

    assert not offenders, (
        "Los errores se comunican con excepciones tipadas, no con string "
        f"matching sobre mensajes: {offenders}"
    )
