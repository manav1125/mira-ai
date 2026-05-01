import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from core.utils.config import EnvMode, config


@dataclass(frozen=True)
class ConfigFinding:
    severity: str
    category: str
    code: str
    message: str
    env_keys: Sequence[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "code": self.code,
            "message": self.message,
            "env_keys": list(self.env_keys),
        }


CORE_DATABASE_KEYS = ("DATABASE_URL", "DATABASE_POOLER_URL")
CORE_REDIS_KEYS = (
    "REDIS_PRIVATE_URL",
    "REDIS_INTERNAL_URL",
    "REDIS_URL",
    "REDIS_URI",
    "REDIS_CONNECTION_STRING",
    "KV_URL",
    "REDIS_HOST",
)
CORE_ENCRYPTION_KEYS = ("MCP_CREDENTIAL_ENCRYPTION_KEY", "ENCRYPTION_KEY")
SUPABASE_KEYS = ("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY")
MAIN_LLM_PROVIDER_KEYS: Dict[str, Sequence[str]] = {
    "anthropic": ("ANTHROPIC_API_KEY",),
    "bedrock": ("AWS_BEARER_TOKEN_BEDROCK", "AWS_ACCESS_KEY_ID"),
    "grok": ("OPENROUTER_API_KEY",),
    "kimi": ("OPENROUTER_API_KEY",),
    "minimax": ("OPENROUTER_API_KEY",),
    "openai": ("OPENAI_API_KEY", "OPENAI_COMPATIBLE_API_KEY", "OPENROUTER_API_KEY"),
}
DOCUMENTED_REQUIRED_ENV_GROUPS: Dict[str, Sequence[str]] = {
    "runtime": ("ENV_MODE",),
    "supabase": SUPABASE_KEYS,
    "database": ("DATABASE_URL", "DATABASE_POOLER_URL"),
    "redis": ("REDIS_INTERNAL_URL", "REDIS_PRIVATE_URL", "REDIS_URL"),
    "security": ("MCP_CREDENTIAL_ENCRYPTION_KEY",),
    "main_llm": ("MAIN_LLM",),
}
DOCUMENTED_OPTIONAL_ENV_GROUPS: Dict[str, Sequence[str]] = {
    "memory": ("MEMORY_EMBEDDING_PROVIDER", "MEMORY_EMBEDDING_MODEL", "VOYAGE_API_KEY", "OPENAI_API_KEY"),
    "sandbox": ("DAYTONA_API_KEY", "DAYTONA_SERVER_URL", "DAYTONA_TARGET"),
    "media": ("REPLICATE_API_TOKEN",),
    "search": ("TAVILY_API_KEY",),
    "scraping": ("FIRECRAWL_API_KEY",),
    "image_search": ("SERPER_API_KEY",),
    "integrations": ("COMPOSIO_API_KEY", "COMPOSIO_WEBHOOK_SECRET"),
    "notifications": ("NOVU_SECRET_KEY",),
    "billing": (
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "REVENUECAT_API_KEY",
        "REVENUECAT_PROJECT_ID",
        "REVENUECAT_WEBHOOK_SECRET",
    ),
    "voice": ("VAPI_PRIVATE_KEY", "VAPI_PUBLIC_KEY", "VAPI_PHONE_NUMBER_ID", "VAPI_WEBHOOK_SECRET"),
    "trust": ("REALITY_DEFENDER_API_KEY",),
    "observability": ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST", "BRAINTRUST_API_KEY"),
}
DIAGNOSTIC_ENDPOINTS: Sequence[str] = ("/v1/health", "/v1/debug/redis", "/v1/debug/config")


def _env_mode() -> EnvMode:
    return config.ENV_MODE or EnvMode.LOCAL


def _is_set(key: str) -> bool:
    value = os.getenv(key)
    return value is not None and value.strip() != ""


def _first_present(keys: Sequence[str]) -> Optional[str]:
    for key in keys:
        if _is_set(key):
            return key
    return None


def _add_any_required(
    findings: List[ConfigFinding],
    category: str,
    code: str,
    message: str,
    keys: Sequence[str],
) -> None:
    if _first_present(keys):
        return
    findings.append(
        ConfigFinding(
            severity="error",
            category=category,
            code=code,
            message=message,
            env_keys=keys,
        )
    )


def _add_all_required(
    findings: List[ConfigFinding],
    category: str,
    code: str,
    message: str,
    keys: Sequence[str],
) -> None:
    missing = [key for key in keys if not _is_set(key)]
    if not missing:
        return
    findings.append(
        ConfigFinding(
            severity="error",
            category=category,
            code=code,
            message=f"{message} Missing: {', '.join(missing)}",
            env_keys=keys,
        )
    )


def _validate_main_llm(findings: List[ConfigFinding]) -> None:
    provider = (getattr(config, "MAIN_LLM", None) or "bedrock").lower()
    keys = MAIN_LLM_PROVIDER_KEYS.get(provider)
    if not keys:
        findings.append(
            ConfigFinding(
                severity="warning",
                category="llm",
                code="UNKNOWN_MAIN_LLM",
                message=f"MAIN_LLM={provider!r} is not recognized by the config validator.",
                env_keys=("MAIN_LLM",),
            )
        )
        return

    if _first_present(keys):
        return

    findings.append(
        ConfigFinding(
            severity="error",
            category="llm",
            code="MAIN_LLM_CREDENTIALS_MISSING",
            message=f"MAIN_LLM is set to '{provider}' but matching provider credentials are missing.",
            env_keys=("MAIN_LLM", *keys),
        )
    )


def _validate_recommendations(findings: List[ConfigFinding]) -> None:
    if not _is_set("SUPABASE_JWT_SECRET"):
        findings.append(
            ConfigFinding(
                severity="warning",
                category="auth",
                code="SUPABASE_JWT_SECRET_MISSING",
                message="SUPABASE_JWT_SECRET is not set; JWT verification will fall back to the Supabase user endpoint.",
                env_keys=("SUPABASE_JWT_SECRET",),
            )
        )

    if not (_is_set("REDIS_PRIVATE_URL") or _is_set("REDIS_INTERNAL_URL")) and _is_set("REDIS_URL"):
        findings.append(
            ConfigFinding(
                severity="warning",
                category="redis",
                code="REDIS_INTERNAL_URL_RECOMMENDED",
                message="REDIS_URL is configured without REDIS_INTERNAL_URL/REDIS_PRIVATE_URL. On Render, prefer a private Redis URL to avoid public-network allowlist issues.",
                env_keys=("REDIS_URL", "REDIS_INTERNAL_URL", "REDIS_PRIVATE_URL"),
            )
        )

    optional_features = [
        ("media", "REPLICATE_API_TOKEN", "Replicate-backed media generation will be unavailable."),
        ("search", "TAVILY_API_KEY", "Web search will be unavailable."),
        ("scraping", "FIRECRAWL_API_KEY", "Firecrawl scraping will be unavailable; fallback scraping may be used."),
        ("sandbox", "DAYTONA_API_KEY", "Sandbox-backed tools will be unavailable."),
        ("integrations", "COMPOSIO_API_KEY", "Composio integrations will be unavailable."),
        ("notifications", "NOVU_SECRET_KEY", "Novu notifications will be unavailable."),
    ]
    for category, key, message in optional_features:
        if _is_set(key):
            continue
        findings.append(
            ConfigFinding(
                severity="warning",
                category=category,
                code=f"{key}_MISSING",
                message=message,
                env_keys=(key,),
            )
        )


def validate_runtime_configuration() -> Dict[str, Any]:
    findings: List[ConfigFinding] = []

    _add_all_required(
        findings,
        category="supabase",
        code="SUPABASE_CORE_MISSING",
        message="Supabase configuration is incomplete.",
        keys=SUPABASE_KEYS,
    )
    _add_any_required(
        findings,
        category="database",
        code="DATABASE_URL_MISSING",
        message="Database connection is not configured.",
        keys=CORE_DATABASE_KEYS,
    )
    _add_any_required(
        findings,
        category="redis",
        code="REDIS_CONFIG_MISSING",
        message="Redis connection is not configured.",
        keys=CORE_REDIS_KEYS,
    )
    _add_any_required(
        findings,
        category="security",
        code="ENCRYPTION_KEY_MISSING",
        message="Credential encryption key is not configured.",
        keys=CORE_ENCRYPTION_KEYS,
    )
    _validate_main_llm(findings)
    _validate_recommendations(findings)

    errors = [finding.as_dict() for finding in findings if finding.severity == "error"]
    warnings = [finding.as_dict() for finding in findings if finding.severity == "warning"]

    status = "ok"
    if errors:
        status = "error"
    elif warnings:
        status = "warning"

    return {
        "status": status,
        "env_mode": _env_mode().value,
        "strict_mode": _env_mode() in (EnvMode.STAGING, EnvMode.PRODUCTION),
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
        "core_presence": {
            "database": bool(_first_present(CORE_DATABASE_KEYS)),
            "redis": bool(_first_present(CORE_REDIS_KEYS)),
            "encryption": bool(_first_present(CORE_ENCRYPTION_KEYS)),
                "supabase": all(_is_set(key) for key in SUPABASE_KEYS),
                "main_llm_credentials": bool(
                    _first_present(
                        MAIN_LLM_PROVIDER_KEYS.get(
                            (getattr(config, "MAIN_LLM", None) or "bedrock").lower(),
                            (),
                        )
                    )
                ),
        },
    }


def documented_env_keys() -> Dict[str, Sequence[str]]:
    return {
        **DOCUMENTED_REQUIRED_ENV_GROUPS,
        **DOCUMENTED_OPTIONAL_ENV_GROUPS,
        "main_llm_provider_credentials": tuple(
            sorted({key for keys in MAIN_LLM_PROVIDER_KEYS.values() for key in keys})
        ),
    }


def supported_main_llm_providers() -> Dict[str, Sequence[str]]:
    return MAIN_LLM_PROVIDER_KEYS


def should_fail_startup(report: Dict[str, Any]) -> bool:
    return report["strict_mode"] and report["summary"]["errors"] > 0
