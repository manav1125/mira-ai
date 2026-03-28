# Configuration Inventory

This file is the checked-in contract for platform configuration. Keep it in sync with Render, local `.env` files, and any secret manager.

## Why config broke before

- Render's `PUT /env-vars` replaces the full env set. If a payload omits keys, those keys are effectively deleted.
- Rollbacks can restore code with different env expectations or defaults.
- Platform-injected env vars can conflict with app-defined vars unless code prefers the right one.

## Source-of-truth rules

1. Treat this file and `backend/.env.example` as the repo contract.
2. Keep real secrets in a secret manager or Render env groups, not only in the Render UI.
3. When updating Render envs programmatically, always read the full set first, merge, then write.
4. After every deploy, check `/v1/health`, `/v1/debug/redis`, and `/v1/debug/config`.

## Backend: hard-required in staging/production

| Group | Env vars | Why |
| --- | --- | --- |
| Runtime | `ENV_MODE` | Controls production vs staging vs local defaults |
| Supabase | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | Auth, DB access, storage |
| Database | `DATABASE_URL` or `DATABASE_POOLER_URL` | Primary backend database connectivity |
| Redis | `REDIS_INTERNAL_URL` or `REDIS_PRIVATE_URL` preferred; `REDIS_URL` fallback | Streams, pending thread state, run cache, queue-like coordination |
| Encryption | `MCP_CREDENTIAL_ENCRYPTION_KEY` | Protects saved credential/integration config |
| Main LLM | `MAIN_LLM`, plus matching provider credential | Required for any agent run to execute |

## Backend: provider mapping for `MAIN_LLM`

| `MAIN_LLM` value | Required credential |
| --- | --- |
| `anthropic` | `ANTHROPIC_API_KEY` |
| `openai` | `OPENAI_API_KEY` or `OPENAI_COMPATIBLE_API_KEY` or `OPENROUTER_API_KEY` |
| `minimax` | `OPENROUTER_API_KEY` |
| `kimi` | `OPENROUTER_API_KEY` |
| `grok` | `OPENROUTER_API_KEY` |
| `bedrock` | `AWS_BEARER_TOKEN_BEDROCK` or AWS access credentials |

## Backend: feature-gated env vars

| Feature | Env vars |
| --- | --- |
| Memory embeddings | `MEMORY_EMBEDDING_PROVIDER`, `MEMORY_EMBEDDING_MODEL`, `VOYAGE_API_KEY`, `OPENAI_API_KEY` |
| Sandboxes | `DAYTONA_API_KEY`, `DAYTONA_SERVER_URL`, `DAYTONA_TARGET` |
| Media generation | `REPLICATE_API_TOKEN` |
| Web search | `TAVILY_API_KEY` |
| Web scraping | `FIRECRAWL_API_KEY` |
| Image search | `SERPER_API_KEY` |
| Integrations | `COMPOSIO_API_KEY`, `COMPOSIO_WEBHOOK_SECRET` |
| Notifications | `NOVU_SECRET_KEY` |
| Billing | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `REVENUECAT_API_KEY`, `REVENUECAT_PROJECT_ID`, `REVENUECAT_WEBHOOK_SECRET` |
| Voice | `VAPI_PRIVATE_KEY`, `VAPI_PUBLIC_KEY`, `VAPI_PHONE_NUMBER_ID`, `VAPI_WEBHOOK_SECRET` |
| Trust & safety | `REALITY_DEFENDER_API_KEY` |
| Observability | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`, `BRAINTRUST_API_KEY` |

## Frontend: required

| Env vars | Why |
| --- | --- |
| `NEXT_PUBLIC_SUPABASE_URL` | Frontend auth/session bootstrap |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Frontend auth/session bootstrap |
| `NEXT_PUBLIC_BACKEND_URL` | All API, streaming, file, and tool requests |
| `NEXT_PUBLIC_URL` or `NEXT_PUBLIC_APP_URL` | Canonical app URL / share URLs |
| `NEXT_PUBLIC_ENV_MODE` | Frontend environment behavior |

## Frontend: optional but important

| Env vars | Why |
| --- | --- |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Web billing checkout |
| `NEXT_PUBLIC_NOVU_APP_IDENTIFIER` | Notification inbox |
| `NEXT_PUBLIC_POSTHOG_KEY` | Product analytics |
| `NEXT_PUBLIC_SYNCFUSION_LICENSE_KEY` | Spreadsheet viewer/editor |
| `NEXT_PUBLIC_DESKTOP_PROTOCOL` | Desktop auth / deep-linking |

## Mobile: optional / feature-based

| Env vars | Why |
| --- | --- |
| `EXPO_PUBLIC_SUPABASE_URL` | Mobile auth |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | Mobile auth |
| `EXPO_PUBLIC_REVENUECAT_IOS_API_KEY` | iOS billing |
| `EXPO_PUBLIC_REVENUECAT_ANDROID_API_KEY` | Android billing |
| `EXPO_PUBLIC_USE_REVENUECAT` | Mobile billing provider selection |

## Operational checklist

Before deploy:

1. Confirm env changes were merged, not replaced.
2. Confirm backend has database, Redis, encryption key, and main LLM credentials.
3. Confirm frontend points to the expected backend URL.

After deploy:

1. `GET /v1/health`
2. `GET /v1/debug/redis`
3. `GET /v1/debug/config`
4. Load thread list
5. Start one trivial agent run

## Notes

- On Render, prefer private Redis URLs over public Redis URLs.
- `SUPABASE_JWT_SECRET` is strongly recommended even though the backend can fall back to remote verification.
- Missing feature env vars should disable the feature clearly, not degrade the whole app.
