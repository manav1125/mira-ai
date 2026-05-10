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
    "internal_webhooks": ("SUPABASE_WEBHOOK_SECRET", "TRIGGER_WEBHOOK_SECRET", "WEBHOOK_BASE_URL"),
    "voice": ("VAPI_PRIVATE_KEY", "VAPI_PUBLIC_KEY", "VAPI_PHONE_NUMBER_ID", "VAPI_WEBHOOK_SECRET"),
    "trust": ("REALITY_DEFENDER_API_KEY",),
    "observability": (
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_HOST",
        "BRAINTRUST_API_KEY",
        "CLOUDWATCH_METRICS_ENABLED",
    ),
}
DIAGNOSTIC_ENDPOINTS: Sequence[str] = ("/v1/health", "/v1/debug/redis", "/v1/debug/config")

FEATURE_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "agent_core": {
        "label": "Core agent runs",
        "category": "core",
        "required_any": (
            ("database", CORE_DATABASE_KEYS),
            ("redis", CORE_REDIS_KEYS),
            ("encryption", CORE_ENCRYPTION_KEYS),
            ("main_llm_credentials", ()),
        ),
        "notes": "Required for new chats, streaming, and tool orchestration.",
    },
    "billing": {
        "label": "Stripe billing and credits",
        "category": "monetization",
        "required_all": ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"),
        "recommended_any": (
            ("launch_tier_price_ids", (
                "STRIPE_TIER_2_20_ID_PROD",
                "STRIPE_TIER_6_50_ID_PROD",
                "STRIPE_TIER_25_200_ID_PROD",
            )),
            ("top_up_price_ids", (
                "STRIPE_CREDITS_10_PRICE_ID_PROD",
                "STRIPE_CREDITS_25_PRICE_ID_PROD",
                "STRIPE_CREDITS_50_PRICE_ID_PROD",
                "STRIPE_CREDITS_100_PRICE_ID_PROD",
            )),
        ),
        "manual_qa": "Run a live checkout/top-up/webhook replay before launch.",
    },
    "mobile_billing": {
        "label": "RevenueCat mobile billing",
        "category": "monetization",
        "required_all": ("REVENUECAT_API_KEY", "REVENUECAT_PROJECT_ID", "REVENUECAT_WEBHOOK_SECRET"),
        "manual_qa": "Validate iOS/Android entitlements and webhook credit grants.",
    },
    "composio_integrations": {
        "label": "Composio app integrations",
        "category": "integrations",
        "required_all": ("COMPOSIO_API_KEY",),
        "recommended_all": ("COMPOSIO_WEBHOOK_SECRET",),
        "config_flags": ("ACTIVATE_MCPS_TRIG",),
        "manual_qa": "Run two-account Gmail isolation and one connected-action test.",
    },
    "custom_mcp": {
        "label": "Custom MCP servers",
        "category": "integrations",
        "required_any": (("credential_encryption", CORE_ENCRYPTION_KEYS),),
        "config_flags": ("ACTIVATE_MCPS_TRIG",),
        "manual_qa": "Install a custom MCP profile and run a tool call.",
    },
    "triggers": {
        "label": "Scheduled and app triggers",
        "category": "automation",
        "required_any": (("redis", CORE_REDIS_KEYS),),
        "recommended_all": ("SUPABASE_WEBHOOK_SECRET",),
        "config_flags": ("ACTIVATE_MCPS_TRIG",),
        "manual_qa": "Create one scheduled trigger and one app-triggered run.",
    },
    "internal_webhooks": {
        "label": "Internal Supabase webhooks",
        "category": "automation",
        "required_all": ("SUPABASE_WEBHOOK_SECRET",),
        "recommended_all": ("WEBHOOK_BASE_URL",),
        "manual_qa": "Run Supabase user-created and stale-project categorization webhooks with matching secrets.",
    },
    "google_exports": {
        "label": "Google Docs/Slides export",
        "category": "exports",
        "required_all": ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"),
        "recommended_all": ("GOOGLE_REDIRECT_URI",),
        "manual_qa": "Complete OAuth and export one generated deck/doc on the current domain.",
    },
    "pdf_pptx_exports": {
        "label": "PDF/PPTX export",
        "category": "exports",
        "required_any": (("sandbox", ("DAYTONA_API_KEY",)),),
        "manual_qa": "Generate a deck and download PDF and PPTX files in browser.",
    },
    "memory": {
        "label": "User memory",
        "category": "personalization",
        "required_any": (
            ("embedding_provider", ("OPENAI_API_KEY", "VOYAGE_API_KEY")),
        ),
        "recommended_any": (
            ("explicit_embedding_config", ("MEMORY_EMBEDDING_PROVIDER", "MEMORY_EMBEDDING_MODEL")),
        ),
        "manual_qa": "Create, retrieve, disable, and delete user and thread memories.",
    },
    "voyage_embeddings": {
        "label": "VoyageAI embeddings",
        "category": "personalization",
        "required_all": ("VOYAGE_API_KEY",),
        "recommended_all": ("MEMORY_EMBEDDING_PROVIDER",),
        "manual_qa": "Set MEMORY_EMBEDDING_PROVIDER=voyageai and run a memory retrieval test.",
    },
    "notifications": {
        "label": "Novu notifications",
        "category": "engagement",
        "required_all": ("NOVU_SECRET_KEY",),
        "manual_qa": "Trigger billing, system, and task notifications for the correct user.",
    },
    "voice": {
        "label": "Vapi voice",
        "category": "voice",
        "required_all": ("VAPI_PRIVATE_KEY", "VAPI_PUBLIC_KEY", "VAPI_PHONE_NUMBER_ID"),
        "recommended_all": ("VAPI_WEBHOOK_SECRET",),
        "manual_qa": "Start a voice call, save transcript, hand off to a thread, and verify billing.",
    },
    "media_generation": {
        "label": "Image/video/media generation",
        "category": "media",
        "required_any": (
            ("media_provider", ("REPLICATE_API_TOKEN", "OPENROUTER_API_KEY")),
        ),
        "manual_qa": "Generate image and video; verify provider failures are actionable.",
    },
    "web_research": {
        "label": "Web research and scraping",
        "category": "research",
        "required_all": ("TAVILY_API_KEY", "FIRECRAWL_API_KEY"),
        "recommended_all": ("SERPER_API_KEY",),
        "manual_qa": "Run search, scrape, image search, and citation-quality checks.",
    },
    "sandbox_runtime": {
        "label": "Daytona sandbox runtime",
        "category": "runtime",
        "required_all": ("DAYTONA_API_KEY",),
        "recommended_all": ("DAYTONA_SERVER_URL", "DAYTONA_TARGET"),
        "manual_qa": "Create a sandbox-backed project and run file/browser/export tools.",
    },
    "sandbox_pool": {
        "label": "Prewarmed sandbox pool",
        "category": "runtime",
        "required_all": ("DAYTONA_API_KEY",),
        "recommended_all": ("SANDBOX_POOL_ENABLED",),
        "manual_qa": "Confirm pool admin page, pool size, claim/release, and idle cleanup.",
    },
    "trust_safety": {
        "label": "Reality Defender trust checks",
        "category": "trust",
        "required_all": ("REALITY_DEFENDER_API_KEY",),
        "manual_qa": "Upload a test asset and verify verdict storage/display.",
    },
    "observability": {
        "label": "Observability and evals",
        "category": "operations",
        "required_any": (
            ("tracing_or_evals", ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "BRAINTRUST_API_KEY")),
        ),
        "recommended_any": (
            ("metrics_sink", ("CLOUDWATCH_METRICS_ENABLED", "LANGFUSE_PUBLIC_KEY", "BRAINTRUST_API_KEY")),
        ),
        "manual_qa": "Verify failed runs include account, thread, run, provider, tool, cost, and error class.",
    },
}


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


def _main_llm_keys() -> Sequence[str]:
    provider = (getattr(config, "MAIN_LLM", None) or "bedrock").lower()
    return MAIN_LLM_PROVIDER_KEYS.get(provider, ())


def _has_group(keys: Sequence[str], *, require_all: bool) -> bool:
    if not keys:
        return False
    if require_all:
        return all(_is_set(key) for key in keys)
    return bool(_first_present(keys))


def _config_flag_enabled(flag: str) -> bool:
    value = getattr(config, flag, None)
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ("true", "t", "yes", "y", "1")


def _evaluate_feature(name: str, definition: Dict[str, Any]) -> Dict[str, Any]:
    missing_required: List[str] = []
    missing_recommended: List[str] = []
    satisfied: List[str] = []
    disabled_by: List[str] = []

    for flag in definition.get("config_flags", ()):
        if not _config_flag_enabled(flag):
            disabled_by.append(flag)

    for key in definition.get("required_all", ()):
        if _is_set(key):
            satisfied.append(key)
        else:
            missing_required.append(key)

    for group_name, group_keys in definition.get("required_any", ()):
        keys = _main_llm_keys() if group_name == "main_llm_credentials" and not group_keys else group_keys
        if _has_group(keys, require_all=False):
            present_key = _first_present(keys)
            satisfied.append(f"{group_name}:{present_key}" if present_key else group_name)
        else:
            missing_required.append(f"{group_name}: one of {', '.join(keys) or 'configured provider credentials'}")

    for key in definition.get("recommended_all", ()):
        if _is_set(key):
            satisfied.append(key)
        else:
            missing_recommended.append(key)

    for group_name, group_keys in definition.get("recommended_any", ()):
        if _has_group(group_keys, require_all=False):
            present_key = _first_present(group_keys)
            satisfied.append(f"{group_name}:{present_key}" if present_key else group_name)
        else:
            missing_recommended.append(f"{group_name}: one of {', '.join(group_keys)}")

    if disabled_by:
        status = "disabled"
    elif missing_required:
        status = "not_configured"
    elif missing_recommended:
        status = "partial"
    else:
        status = "configured"

    return {
        "name": name,
        "label": definition["label"],
        "category": definition["category"],
        "status": status,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "satisfied": satisfied,
        "disabled_by": disabled_by,
        "manual_qa": definition.get("manual_qa"),
        "notes": definition.get("notes"),
    }


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
        ("billing", "STRIPE_SECRET_KEY", "Stripe checkout and subscription management will be unavailable."),
        ("billing", "STRIPE_WEBHOOK_SECRET", "Stripe webhook signature verification will be unavailable."),
        ("webhooks", "SUPABASE_WEBHOOK_SECRET", "Supabase-created users and internal cron hooks may fail authentication."),
        ("google", "GOOGLE_CLIENT_ID", "Google Docs/Slides export OAuth will be unavailable."),
        ("google", "GOOGLE_CLIENT_SECRET", "Google Docs/Slides export OAuth will be unavailable."),
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


def validate_feature_readiness() -> Dict[str, Any]:
    features = {
        name: _evaluate_feature(name, definition)
        for name, definition in FEATURE_REQUIREMENTS.items()
    }

    counts: Dict[str, int] = {}
    categories: Dict[str, Dict[str, int]] = {}
    for feature in features.values():
        status = feature["status"]
        category = feature["category"]
        counts[status] = counts.get(status, 0) + 1
        if category not in categories:
            categories[category] = {}
        categories[category][status] = categories[category].get(status, 0) + 1

    blocking = [
        name
        for name, feature in features.items()
        if name in ("agent_core", "billing") and feature["status"] in ("disabled", "not_configured")
    ]

    status = "ok"
    if blocking:
        status = "error"
    elif any(feature["status"] == "not_configured" for feature in features.values()):
        status = "partial"

    return {
        "status": status,
        "env_mode": _env_mode().value,
        "summary": counts,
        "categories": categories,
        "blocking": blocking,
        "features": features,
        "manual_qa_required": [
            name for name, feature in features.items()
            if feature.get("manual_qa") and feature["status"] in ("configured", "partial")
        ],
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
