# Mira Production Testing Plan

Last updated: 2026-05-01

This plan is designed to answer one question before launch: can a real customer sign up, create useful work, export/share it, manage billing, and trust that their private integrations and data stay isolated?

## Test Levels

| Level | Purpose | Cadence |
| --- | --- | --- |
| P0 launch smoke | Proves the app is reachable and core dependencies are wired correctly | Every deploy |
| P0 authenticated happy path | Proves a real user can complete the core product loop | Every deploy and before launch |
| P1 integration checks | Proves external tools work and do not leak across users | Before launch and weekly |
| P1 billing and cost checks | Proves credits, subscriptions, top-ups, and margins behave correctly | Before launch and on billing changes |
| P2 quality/regression checks | Proves output quality, edge cases, and performance stay acceptable | Weekly and before major launches |

## Executed Checks

| Area | Test | Method | Result | Notes |
| --- | --- | --- | --- | --- |
| Live backend | Health endpoint | `curl https://suna-backend-3teh.onrender.com/v1/health` | PASS | Returned `{"status":"ok"}` with instance id. |
| Live backend | Redis endpoint | `curl https://suna-backend-3teh.onrender.com/v1/debug/redis` | PASS | Redis reported healthy, low latency, active pool stats. |
| Live backend | Config endpoint | `curl https://suna-backend-3teh.onrender.com/v1/debug/config` | PASS | Endpoint is live. Report has zero errors and zero warnings. |
| Live frontend | Frontend availability | `curl -I https://mira-frontend-d85v.onrender.com` | PASS | Returned HTTP 200. |
| Live security | Unauthenticated threads endpoint | `curl https://suna-backend-3teh.onrender.com/v1/threads` | PASS | Returned 401 as expected. |
| Live tools | Canvas/media health | `curl https://suna-backend-3teh.onrender.com/v1/canvas-ai/health` | PASS | OpenRouter and Replicate reported configured. |
| Live tools | Composio health | `curl https://suna-backend-3teh.onrender.com/v1/composio/health` | PASS | Returned healthy. |
| Live smoke suite | Repeatable smoke script | `scripts/production_smoke_check.sh` | PASS | All public smoke checks pass. |
| Backend code | Syntax compilation | `python3 -m compileall ...` | PASS | Key backend files compiled successfully. |
| Backend tests | Config/pricing unit tests | `python3 -m pytest ...` | BLOCKED | `pytest` is not installed in the active Python environment and `uv` is not installed. |
| Frontend tests | TypeScript check | `pnpm --dir apps/frontend exec tsc --noEmit --pretty false` | BLOCKED | Command produced no output and did not complete within the smoke-test window. |
| Frontend tests | Lint check | `pnpm --dir apps/frontend run lint` | BLOCKED | Command invoked `next lint` but did not complete within the smoke-test window. |
| Full E2E | Authenticated user flow | Existing `backend/tests/e2e/test_full_flow.py` | BLOCKED | Requires `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_JWT_SECRET`; not loaded in this shell. |

## P0 Launch Tests

| Area | Test | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- |
| Availability | Frontend loads | Open production dashboard and hard refresh | App shell loads, no infinite skeletons | PARTIAL PASS |
| Availability | Backend health | Call `/v1/health` | HTTP 200 and `status=ok` | PASS |
| Config | Runtime config contract | Call `/v1/debug/config` after deploy | HTTP 200 and required provider groups reported | PASS |
| Database | Authenticated thread list | Sign in and load `/dashboard` | Threads list loads without DB/connection error | BLOCKED |
| Chat loop | Send basic message | Create new chat, send "write a 3 sentence summary of Mira" | Assistant replies and run completes | BLOCKED |
| Agent loop | Start tool-using run | Ask for a short research summary with one web source | Web search/scrape action completes and final answer appears | BLOCKED |
| Files | Create document | Ask for a one-page wiki file | File appears in MiraComputer and can be reopened | BLOCKED |
| Presentations | Create slides | Ask for a 5-slide deck from provided text | Slides render, persist, and match source content | BLOCKED |
| Export | Export PDF/PPTX | Export the generated deck as PDF and PPTX | Browser downloads files successfully | BLOCKED |
| Billing | Plan and credits load | Open billing settings | Current plan, credits, usage, and top-up controls load | BLOCKED |
| Security | Unauth access blocked | Call user-scoped APIs without token | HTTP 401/403, no data returned | PASS |

## P1 Integration Tests

| Integration | Test | Expected Result | Status |
| --- | --- | --- | --- |
| Composio Gmail | Connect one user and fetch unread email | User sees only their own Gmail data | BLOCKED |
| Composio isolation | Two users connect different Gmail accounts | User A cannot access User B's emails or actions | BLOCKED, must run before launch |
| Google Slides export | OAuth flow and deck creation | No `invalid_client`; created Google Slides opens | IN PROGRESS |
| Google Drive files | Upload/read/export file | File is saved under correct user/project scope | BLOCKED |
| Daytona | Sandbox resolution | New project gets a sandbox and tool execution succeeds | BLOCKED |
| Firecrawl/Tavily/Serper | Research workflows | Search and scrape actions complete with citations | BLOCKED |
| Replicate/OpenRouter | Image/video generation | Media task resolves provider and returns output or clear provider error | BLOCKED |
| Novu | Notifications | Trial/credit/payment notifications route to correct user | NOT RUN |
| Vapi | Voice call | Voice call starts, authenticates user scope, logs result | NOT RUN |
| Reality Defender | Deepfake check | Upload returns detection verdict and stores result | NOT RUN |

## P1 Billing And Unit Economics Tests

| Area | Test | Expected Result | Status |
| --- | --- | --- | --- |
| Credits | LLM usage attribution | Every model call records provider, model, input/output tokens, cost, markup, and source action | BLOCKED |
| Pricing | 2x cost markup | Credit charge is at least 100% margin over raw LLM cost | BLOCKED |
| Plans | Monthly allowance | Free/Pro/Business/Enterprise grant correct monthly credits | BLOCKED |
| Top-ups | One-time purchase | Stripe payment grants credits exactly once | BLOCKED |
| Webhooks | Idempotency | Replayed Stripe webhook does not double-credit account | READY TO RUN, Stripe secret and webhook secret are now present in Render; replay a signed event against `/v1/billing/webhook` |
| Exhaustion | Low credits | User gets clear warning and cannot silently run expensive agents past limit | BLOCKED |
| Admin | Usage dashboard | Internal view shows account-level cost, revenue, margin, and provider breakdown | BLOCKED |

## P1 Technical Readiness Tests

| Area | Test | Expected Result | Status |
| --- | --- | --- | --- |
| Deploy safety | Render services use correct repo/branch | Mira frontend, backend, and Redis all point at `mira-ai` and expected branch | PASS |
| Env safety | Env inventory is complete | Required env groups are present in Render and documented | PASS, production `/v1/debug/config` reports zero errors and zero warnings |
| CI | Config guard | CI fails if required production env contract is missing | PRESENT IN CODE, NEEDS LIVE CONFIRMATION |
| CI | Backend E2E workflow | Workflow targets Mira Render URLs, not legacy Kortix URLs | PRESENT IN CODE, dispatch blocked until GitHub PAT has repository `Actions: Read and write` |
| Observability | Logs and traces | Failed runs include run id, user id, provider, tool, and error class | NEEDS VERIFICATION |
| Rate limiting | Abuse protection | API and expensive tool endpoints enforce user/account limits | NEEDS VERIFICATION |
| Data retention | User deletion | Account deletion removes or anonymizes user data and integrations | NEEDS VERIFICATION |

## P2 Output Quality Tests

| Feature | Test | Expected Result | Status |
| --- | --- | --- | --- |
| Slides | Template-content fit | Content maps to template sections instead of generic filler | NEEDS MANUAL QA |
| Slides | Image replacement | Template placeholder images are replaced with relevant assets or removed | NEEDS MANUAL QA |
| Docs | Long-form generation | Wiki/PRD output is complete, structured, and saved as a file | NEEDS MANUAL QA |
| Research | Source quality | Research output cites current, relevant, high-authority sources | NEEDS MANUAL QA |
| Media | Failure handling | Provider errors are actionable and not generic apologies | NEEDS MANUAL QA |

## Required Test Credentials

These should be loaded into a secure local test shell or CI secret store, not committed:

| Secret | Used For |
| --- | --- |
| `TEST_API_URL` | Point E2E tests at production/staging backend |
| `SUPABASE_URL` | Create test users |
| `SUPABASE_SERVICE_ROLE_KEY` | Create/delete isolated test users |
| `SUPABASE_JWT_SECRET` | Mint authenticated test JWTs |
| Stripe test keys and webhook secret | Billing tests |
| Test Gmail/Google account credentials | Composio isolation and Google export tests |

## Recommended Commands

```bash
# Backend focused tests
python3 -m pytest backend/tests/core/test_config_validation.py backend/tests/core/test_config_contract.py backend/tests/core/test_pricing_unit_economics.py -q

# Full authenticated API flow, once Supabase test env vars are loaded
TEST_API_URL=https://suna-backend-3teh.onrender.com/v1 \
python3 -m pytest backend/tests/e2e/test_full_flow.py::test_complete_api_flow -v

# Frontend static verification
pnpm --dir apps/frontend exec tsc --noEmit --pretty false
pnpm --dir apps/frontend run lint

# Live smoke checks
scripts/production_smoke_check.sh
curl -fsS https://suna-backend-3teh.onrender.com/v1/health
curl -fsS https://suna-backend-3teh.onrender.com/v1/debug/redis
curl -fsS https://suna-backend-3teh.onrender.com/v1/debug/config
curl -I -fsS https://mira-frontend-d85v.onrender.com
```

## Launch Gate

Do not mark production launch-ready until these are green:

1. `SUPABASE_JWT_SECRET` is set in Render and matching production/staging CI secrets are available.
2. Authenticated full E2E flow passes against production or staging.
3. Composio two-user isolation test passes.
4. Google Slides, PDF, and PPTX exports work from a generated deck.
5. Credits usage records raw cost, marked-up credit charge, and gross margin per action.
6. CI workflows target Mira Render URLs and the `mira-ai` repo/branch, not legacy Kortix endpoints.
