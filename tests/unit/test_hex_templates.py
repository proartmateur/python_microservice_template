import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_ROOT = PROJECT_ROOT / ".gen_cli" / "templates" / "hex"


def test_hex_architecture_registers_the_base_templates() -> None:
    architectures = json.loads((PROJECT_ROOT / "arq.json").read_text())
    hex_architecture = next(item for item in architectures if item["option"] == "--hex")

    destinations = {
        template["destination"] for template in hex_architecture["templates"]
    }

    assert "<path>/domain/entities.py" in destinations
    assert "<path>/domain/repositories.py" in destinations
    assert "<path>/domain/exceptions.py" in destinations
    assert "<path>/infrastructure/persistence/models.py" in destinations
    assert "<path>/infrastructure/persistence/repositories.py" in destinations
    assert "<path>/infrastructure/http/dependencies.py" in destinations
    assert all("routers.py" not in destination for destination in destinations)


def test_hex_templates_expose_mutation_markers() -> None:
    expected_markers = {
        "repositories_port_template.py": "# gencli:repository-port-methods",
        "repositories_adapter_template.py": "# gencli:repository-adapter-methods",
        "dependencies_template.py": "# gencli:use-case-providers",
    }

    for filename, marker in expected_markers.items():
        assert marker in (TEMPLATES_ROOT / filename).read_text()


def test_uc_list_registers_a_single_post_generation_hook() -> None:
    architectures = json.loads((PROJECT_ROOT / "arq.json").read_text())
    uc_list = next(item for item in architectures if item["option"] == "--uc-list")
    hooks = [
        template["onDone"]
        for template in uc_list["templates"]
        if "onDone" in template
    ]

    assert hooks == [
        "python .gen_cli/scripts/register_uc_list.py "
        '<destination> <ent> <snake_name> "<inline_props>"'
    ]


def test_hex_property_blocks_preserve_python_indentation() -> None:
    # GenCLI v2.1 removes the opening parenthesis and one following character.
    expected_prefix = "(     $snake_prop$:"

    assert expected_prefix in (TEMPLATES_ROOT / "entities_template.py").read_text()
    assert expected_prefix in (TEMPLATES_ROOT / "models_template.py").read_text()
