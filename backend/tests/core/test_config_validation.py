from types import SimpleNamespace

from core.utils.config import EnvMode, config
from core.utils.config_validation import (
    DOCUMENTED_OPTIONAL_ENV_GROUPS,
    validate_feature_readiness,
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
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "GOOGLE_REDIRECT_URI",
        "REVENUECAT_API_KEY",
        "REVENUECAT_PROJECT_ID",
        "REVENUECAT_WEBHOOK_SECRET",
        "VAPI_PRIVATE_KEY",
        "VAPI_PUBLIC_KEY",
        "VAPI_PHONE_NUMBER_ID",
        "VAPI_WEBHOOK_SECRET",
        "MEMORY_EMBEDDING_PROVIDER",
        "MEMORY_EMBEDDING_MODEL",
        "VOYAGE_API_KEY",
        "REALITY_DEFENDER_API_KEY",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "BRAINTRUST_API_KEY",
        "SANDBOX_POOL_ENABLED",
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
        "GOOGLE_CLIENT_ID": "google-client",
        "GOOGLE_CLIENT_SECRET": "google-secret",
        "STRIPE_SECRET_KEY": "stripe-secret",
        "STRIPE_WEBHOOK_SECRET": "stripe-webhook",
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


def test_warns_when_billing_credentials_are_missing(monkeypatch):
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
        "GOOGLE_CLIENT_ID": "google-client",
        "GOOGLE_CLIENT_SECRET": "google-secret",
    }

    for key, value in required_env.items():
        monkeypatch.setenv(key, value)

    report = validate_runtime_configuration()
    warning_codes = {entry["code"] for entry in report["warnings"]}

    assert report["status"] == "warning"
    assert report["summary"]["errors"] == 0
    assert "STRIPE_SECRET_KEY_MISSING" in warning_codes
    assert "STRIPE_WEBHOOK_SECRET_MISSING" in warning_codes
    assert should_fail_startup(report) is False


def test_feature_readiness_reports_configured_partial_and_not_configured(monkeypatch):
    _clear_env(monkeypatch)
    _set_runtime_config(monkeypatch, env_mode=EnvMode.PRODUCTION, main_llm="anthropic")
    monkeypatch.setattr(config, "ACTIVATE_MCPS_TRIG", True)

    required_env = {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_ANON_KEY": "anon",
        "SUPABASE_SERVICE_ROLE_KEY": "service",
        "DATABASE_URL": "postgresql://postgres:password@localhost:5432/postgres",
        "REDIS_INTERNAL_URL": "redis://private-redis:6379",
        "MCP_CREDENTIAL_ENCRYPTION_KEY": "secret",
        "ANTHROPIC_API_KEY": "anthropic",
        "STRIPE_SECRET_KEY": "stripe-secret",
        "STRIPE_WEBHOOK_SECRET": "stripe-webhook",
        "STRIPE_TIER_2_20_ID_PROD": "plus",
        "STRIPE_TIER_6_50_ID_PROD": "pro",
        "STRIPE_TIER_25_200_ID_PROD": "ultra",
        "STRIPE_CREDITS_10_PRICE_ID_PROD": "topup",
        "COMPOSIO_API_KEY": "composio",
        "GOOGLE_CLIENT_ID": "google-client",
        "GOOGLE_CLIENT_SECRET": "google-secret",
        "DAYTONA_API_KEY": "daytona",
    }

    for key, value in required_env.items():
        monkeypatch.setenv(key, value)

    report = validate_feature_readiness()

    assert report["status"] == "partial"
    assert report["features"]["agent_core"]["status"] == "configured"
    assert report["features"]["billing"]["status"] == "configured"
    assert report["features"]["composio_integrations"]["status"] == "partial"
    assert report["features"]["google_exports"]["status"] == "partial"
    assert report["features"]["voice"]["status"] == "not_configured"
    assert "billing" not in report["blocking"]
    assert "composio_integrations" in report["manual_qa_required"]


def test_feature_readiness_marks_mcp_features_disabled_when_flag_is_off(monkeypatch):
    _clear_env(monkeypatch)
    _set_runtime_config(monkeypatch, env_mode=EnvMode.PRODUCTION, main_llm="anthropic")
    monkeypatch.setattr(config, "ACTIVATE_MCPS_TRIG", False)

    monkeypatch.setenv("MCP_CREDENTIAL_ENCRYPTION_KEY", "secret")
    monkeypatch.setenv("COMPOSIO_API_KEY", "composio")

    report = validate_feature_readiness()

    assert report["features"]["composio_integrations"]["status"] == "disabled"
    assert report["features"]["custom_mcp"]["status"] == "disabled"
    assert report["features"]["triggers"]["status"] == "disabled"
