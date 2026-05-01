import re
from pathlib import Path

from core.utils.config_validation import (
    DIAGNOSTIC_ENDPOINTS,
    DOCUMENTED_OPTIONAL_ENV_GROUPS,
    DOCUMENTED_REQUIRED_ENV_GROUPS,
    supported_main_llm_providers,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ENV_EXAMPLE = REPO_ROOT / "backend" / ".env.example"
CONFIG_INVENTORY = REPO_ROOT / "docs" / "configuration-inventory.md"
BACKEND_API = REPO_ROOT / "backend" / "api.py"


def _env_example_keys() -> set[str]:
    keys = set()
    for line in BACKEND_ENV_EXAMPLE.read_text().splitlines():
        match = re.match(r"^([A-Z0-9_]+)=", line.strip())
        if match:
            keys.add(match.group(1))
    return keys


def test_backend_env_example_covers_documented_contract():
    env_keys = _env_example_keys()
    expected_keys = {
        key
        for group in (
            DOCUMENTED_REQUIRED_ENV_GROUPS,
            DOCUMENTED_OPTIONAL_ENV_GROUPS,
            supported_main_llm_providers(),
        )
        for keys in group.values()
        for key in keys
    }

    missing = sorted(expected_keys - env_keys)
    assert missing == []


def test_config_inventory_mentions_required_endpoints_and_keys():
    inventory_text = CONFIG_INVENTORY.read_text()

    for endpoint in DIAGNOSTIC_ENDPOINTS:
        assert endpoint in inventory_text

    for keys in DOCUMENTED_REQUIRED_ENV_GROUPS.values():
        for key in keys:
            assert f"`{key}`" in inventory_text


def test_backend_api_exposes_runtime_config_endpoint():
    api_text = BACKEND_API.read_text()

    assert '"/debug/config"' in api_text
    assert "validate_runtime_configuration()" in api_text
