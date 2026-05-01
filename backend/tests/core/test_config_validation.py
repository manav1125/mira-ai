from types import SimpleNamespace

from core.utils.config import EnvMode, config
from core.utils.config_validation import (
    DOCUMENTED_OPTIONAL_ENV_GROUPS,
    validate_runtime_configuration,
    should_fail_startup,
)


def _set_runtime_config(monkeypatch, *, env_mode: EnvMode, main_llm: str) -> None:
    monkeypatch.setattr(
        config,
        "_config",
        SimpleNamespace(ENV_MODE=env_mode, MAIN_LLM=main_llm),
    )


def _clear_env(monkeypatch) -> None:
    candidate_keys = {
        "ENV_MODE",
        "MAIN_LLM",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_JWT_SECRET",
        "DATABASE_URL",
        "DATABASE_POOLER_URL",
        "REDIS_PRIVATE_URL",
        "REDIS_INTERNAL_URL",
        "REDIS_URL",
        "REDIS_URI",
        "REDIS_CONNECTION_STRING",
        "KV_URL",
        "REDIS_HOST",
        "MCP_CREDENTIAL_ENCRYPTION_KEY",
        "ENCRYPTION_KEY",
        "ANTHROPIC_API_KEY",
        "OPENROUTER_API_KEY",
        "OPENAI_API_KEY",
        "OPENAI_COMPATIBLE_API_KEY",
        "AWS_BEARER_TOKEN_BEDROCK",
        "AWS_ACCESS_KEY_ID",
    }
    for keys in DOCUMENTED_OPTIONAL_ENV_GROUPS.values():
        candidate_keys.update(keys)

    for key in candidate_keys:
        monkeypatch.delenv(key, raising=False)


def test_reports_core_errors_when_required_config_is_missing(monkeypatch):
    _clear_env(monkeypatch)
    _set_runtime_config(monkeypatch, env_mode=EnvMode.STAGING, main_llm="anthropic")

    report = validate_runtime_configuration()
    error_codes = {entry["code"] for entry in report["errors"]}

    assert report["status"] == "error"
    assert report["strict_mode"] is True
    assert "SUPABASE_CORE_MISSING" in error_codes
    assert "DATABASE_URL_MISSING" in error_codes
    assert "REDIS_CONFIG_MISSING" in error_codes
    assert "ENCRYPTION_KEY_MISSING" in error_codes
    assert "MAIN_LLM_CREDENTIALS_MISSING" in error_codes
    assert should_fail_startup(report) is True


def test_warns_when_only_public_redis_url_is_configured(monkeypatch):
    _clear_env(monkeypatch)
    _set_runtime_config(monkeypatch, env_mode=EnvMode.LOCAL, main_llm="anthropic")

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "jwt")
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/postgres")
    monkeypatch.setenv("REDIS_URL", "redis://public-redis:6379")
    monkeypatch.setenv("MCP_CREDENTIAL_ENCRYPTION_KEY", "secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic")

    report = validate_runtime_configuration()
    warning_codes = {entry["code"] for entry in report["warnings"]}

    assert report["summary"]["errors"] == 0
    assert "REDIS_INTERNAL_URL_RECOMMENDED" in warning_codes
    assert should_fail_startup(report) is False


def test_returns_ok_when_full_documented_stack_is_present(monkeypatch):
    _clear_env(monkeypatch)
    _set_runtime_config(monkeypatch, env_mode=EnvMode.PRODUCTION, main_llm="anthropic")

    required_env = {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_ANON_KEY": "anon",
        "SUPABASE_SERVICE_ROLE_KEY": "service",
        "SUPABASE_JWT_SECRET": "jwt",
        "DATABASE_URL": "postgresql://postgres:password@localhost:5432/postgres",
        "REDIS_INTERNAL_URL": "redis://private-redis:6379",
        "MCP_CREDENTIAL_ENCRYPTION_KEY": "secret",
        "ANTHROPIC_API_KEY": "anthropic",
        "DAYTONA_API_KEY": "daytona",
        "REPLICATE_API_TOKEN": "replicate",
        "TAVILY_API_KEY": "tavily",
        "FIRECRAWL_API_KEY": "firecrawl",
        "COMPOSIO_API_KEY": "composio",
        "NOVU_SECRET_KEY": "novu",
    }

    for key, value in required_env.items():
        monkeypatch.setenv(key, value)

    report = validate_runtime_configuration()

    assert report["status"] == "ok"
    assert report["summary"] == {"errors": 0, "warnings": 0}
    assert report["core_presence"] == {
        "database": True,
        "redis": True,
        "encryption": True,
        "supabase": True,
        "main_llm_credentials": True,
    }
    assert should_fail_startup(report) is False
