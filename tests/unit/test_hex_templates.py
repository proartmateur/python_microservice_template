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
    assert "<path>/infrastructure/http/routers.py" in destinations
    assert "<path>/infrastructure/http/schemas.py" in destinations

    routers_template = next(
        template
        for template in hex_architecture["templates"]
        if template["destination"] == "<path>/infrastructure/http/routers.py"
    )
    assert "onDone" not in routers_template


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
        template["onDone"] for template in uc_list["templates"] if "onDone" in template
    ]

    assert hooks == [
        "python .gen_cli/scripts/register_uc_list.py "
        '<destination> <ent> <snake_name> "<inline_props>"'
    ]


def test_uc_list_paginated_registers_a_single_post_generation_hook() -> None:
    architectures = json.loads((PROJECT_ROOT / "arq.json").read_text())
    uc_list_paginated = next(
        item for item in architectures if item["option"] == "--uc-list-paginated"
    )
    hooks = [
        template["onDone"]
        for template in uc_list_paginated["templates"]
        if "onDone" in template
    ]

    assert hooks == [
        "python .gen_cli/scripts/register_uc_list_paginated.py "
        '<destination> <ent> <snake_name> "<inline_props>"'
    ]


def test_uc_find_by_registers_a_single_post_generation_hook() -> None:
    architectures = json.loads((PROJECT_ROOT / "arq.json").read_text())
    uc_find_by = next(
        item for item in architectures if item["option"] == "--uc-find-by"
    )
    hooks = [
        template["onDone"]
        for template in uc_find_by["templates"]
        if "onDone" in template
    ]

    assert hooks == [
        "python .gen_cli/scripts/register_uc_find_by.py "
        '<destination> <ent> <snake_name> "<inline_props>"'
    ]


def test_write_use_cases_register_a_single_post_generation_hook() -> None:
    architectures = json.loads((PROJECT_ROOT / "arq.json").read_text())

    for option, script in (
        ("--uc-create", "register_uc_create.py"),
        ("--uc-get", "register_uc_get.py"),
        ("--uc-update", "register_uc_update.py"),
        ("--uc-delete", "register_uc_delete.py"),
    ):
        architecture = next(item for item in architectures if item["option"] == option)
        hooks = [
            template["onDone"]
            for template in architecture["templates"]
            if "onDone" in template
        ]
        assert hooks == [
            f"python .gen_cli/scripts/{script} "
            '<destination> <ent> <snake_name> "<inline_props>"'
        ]


def test_hex_property_blocks_preserve_python_indentation() -> None:
    # GenCLI v2.1 removes the opening parenthesis and one following character.
    expected_prefix = "(     $snake_prop$:"

    assert expected_prefix in (TEMPLATES_ROOT / "entities_template.py").read_text()
    assert expected_prefix in (TEMPLATES_ROOT / "models_template.py").read_text()
