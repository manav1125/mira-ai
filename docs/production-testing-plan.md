# Mira Production Testing Plan

Last updated: 2026-05-02

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
| Live backend | Feature readiness endpoint | `curl https://suna-backend-3teh.onrender.com/v1/debug/features` | NEW | Reports optional modules as configured, partial, not configured, or disabled without exposing secrets. |
| Live frontend | Frontend availability | `curl -I https://mira-frontend-d85v.onrender.com` | PASS | Returned HTTP 200. |
| Live security | Unauthenticated threads endpoint | `curl https://suna-backend-3teh.onrender.com/v1/threads` | PASS | Returned 401 as expected. |
| Live tools | Canvas/media health | `curl https://suna-backend-3teh.onrender.com/v1/canvas-ai/health` | PASS | OpenRouter and Replicate reported configured. |
| Live tools | Composio health | `curl https://suna-backend-3teh.onrender.com/v1/composio/health` | PASS | Returned healthy. |
| Live smoke suite | Repeatable smoke script | `scripts/production_smoke_check.sh` | PASS | All public smoke checks pass. |
| Backend code | Syntax compilation | `python3 -m compileall ...` | PASS | Key backend files compiled successfully. |
| Backend tests | Config/pricing/unit isolation tests | `mise exec -- bash -lc 'cd backend && uv run pytest --noconftest ... -q'` | PASS | Config, Composio isolation, Stripe idempotency, and pricing tests pass locally. |
| Frontend tests | TypeScript check | `pnpm --dir apps/frontend exec tsc --noEmit --pretty false` | BLOCKED | Command produced no output and did not complete within the smoke-test window. |
| Frontend tests | Lint check | `pnpm --dir apps/frontend run lint` | BLOCKED | Command invoked `next lint` but did not complete within the smoke-test window. |
| Full E2E | Authenticated user flow | GitHub Actions `e2e-api-tests.yml` against production | PASS | Production E2E runs passed after CI secrets and Mira URLs were corrected. |
| Live integrations | Synthetic Composio profile isolation | Two live test users, one credential profile, cross-user access probes | PASS | Owner read returned `200`; cross-user profile and MCP URL access returned `403`. |
| Billing | Stripe webhook replay | Signed smoke event against `/v1/billing/webhook` | PASS | Endpoint URL/events were corrected; replay returned `200` and webhook event persisted. |

## P0 Launch Tests

| Area | Test | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- |
| Availability | Frontend loads | Open production dashboard and hard refresh | App shell loads, no infinite skeletons | PARTIAL PASS |
| Availability | Backend health | Call `/v1/health` | HTTP 200 and `status=ok` | PASS |
| Config | Runtime config contract | Call `/v1/debug/config` after deploy | HTTP 200 and required provider groups reported | PASS |
| Config | Feature readiness contract | Call `/v1/debug/features` after deploy | HTTP 200 and optional launch features are categorized | AUTOMATED |
| Database | Authenticated thread list | Sign in and load `/dashboard` | Threads list loads without DB/connection error | NEEDS MANUAL QA |
| Chat loop | Send basic message | Create new chat, send "write a 3 sentence summary of Mira" | Assistant replies and run completes | NEEDS MANUAL QA |
| Agent loop | Start tool-using run | Ask for a short research summary with one web source | Web search/scrape action completes and final answer appears | NEEDS MANUAL QA |
| Files | Create document | Ask for a one-page wiki file | File appears in MiraComputer and can be reopened | NEEDS MANUAL QA |
| Presentations | Create slides | Ask for a 5-slide deck from provided text | Slides render, persist, and match source content | NEEDS MANUAL QA |
| Export | Export PDF/PPTX | Export the generated deck as PDF and PPTX | Browser downloads files successfully | NEEDS MANUAL QA |
| Billing | Plan and credits load | Open billing settings | Current plan, credits, usage, and top-up controls load | NEEDS MANUAL QA |
| Security | Unauth access blocked | Call user-scoped APIs without token | HTTP 401/403, no data returned | PASS |

## P1 Integration Tests

| Integration | Test | Expected Result | Status |
| --- | --- | --- | --- |
| Composio Gmail | Connect one user and fetch unread email | User sees only their own Gmail data | READY FOR USER QA |
| Composio isolation | Two users connect different Gmail accounts | User A cannot access User B's emails or actions | READY FOR USER QA, must pass before launch |
| Google Slides export | OAuth flow and deck creation | No `invalid_client`; created Google Slides opens | READY FOR USER QA on current Render callback; final domain cutover later |
| Google Drive files | Upload/read/export file | File is saved under correct user/project scope | READY FOR USER QA |
| Daytona | Sandbox resolution | New project gets a sandbox and tool execution succeeds | NEEDS MANUAL QA |
| Firecrawl/Tavily/Serper | Research workflows | Search and scrape actions complete with citations | NEEDS MANUAL QA |
| Replicate/OpenRouter | Image/video generation | Media task resolves provider and returns output or clear provider error | NEEDS MANUAL QA |
| Novu | Notifications | Trial/credit/payment notifications route to correct user | NOT RUN |
| Vapi | Voice call | Voice call starts, authenticates user scope, logs result | NOT RUN |
| Reality Defender | Deepfake check | Upload returns detection verdict and stores result | NOT RUN |

## P1 Billing And Unit Economics Tests

| Area | Test | Expected Result | Status |
| --- | --- | --- | --- |
| Credits | LLM usage attribution | Every model call records provider, model, input/output tokens, cost, markup, and source action | PASS IN UNIT TESTS, NEEDS LIVE SPOT CHECK |
| Pricing | 2x cost markup | Credit charge is at least 100% margin over raw LLM cost | PASS IN UNIT TESTS |
| Plans | Monthly allowance | Free/Pro/Business/Enterprise grant correct monthly credits | BLOCKED |
| Top-ups | One-time purchase | Stripe payment grants credits exactly once | BLOCKED |
| Webhooks | Idempotency | Replayed Stripe webhook does not double-credit account | PASS IN UNIT TESTS; signed webhook smoke passed |
| Exhaustion | Low credits | User gets clear warning and cannot silently run expensive agents past limit | BLOCKED |
| Admin | Usage dashboard | Internal view shows account-level cost, revenue, margin, and provider breakdown | BLOCKED |

## P1 Technical Readiness Tests

| Area | Test | Expected Result | Status |
| --- | --- | --- | --- |
| Deploy safety | Render services use correct repo/branch | Mira frontend, backend, and Redis all point at `mira-ai` and expected branch | PASS |
| Env safety | Env inventory is complete | Required env groups are present in Render and documented | PASS, production `/v1/debug/config` reports zero errors and zero warnings |
| CI | Config guard | CI fails if required production env contract is missing | PASS |
| CI | Backend E2E workflow | Workflow targets Mira Render URLs, not legacy Kortix URLs | PASS |
| Observability | Logs and traces | Failed runs include run id, user id, provider, tool, and error class | NEEDS VERIFICATION |
| Rate limiting | Abuse protection | API and expensive tool endpoints enforce user/account limits | NEEDS VERIFICATION |
| Data retention | User deletion | Account deletion removes or anonymizes user data and integrations | CODED, SQL MIGRATION NOT APPLIED |

## P2 Output Quality Tests

| Feature | Test | Expected Result | Status |
| --- | --- | --- | --- |
| Slides | Template-content fit | Content maps to template sections instead of generic filler | NEEDS MANUAL QA |
| Slides | Image replacement | Template placeholder images are replaced with relevant assets or removed | NEEDS MANUAL QA |
| Docs | Long-form generation | Wiki/PRD output is complete, structured, and saved as a file | NEEDS MANUAL QA |
| Research | Source quality | Research output cites current, relevant, high-authority sources | NEEDS MANUAL QA |
| Media | Failure handling | Provider errors are actionable and not generic apologies | NEEDS MANUAL QA |

## Current Real-User Integration QA

Use two separate browser profiles or one normal window plus one incognito window. Sign into Mira with two different users, then connect a different Gmail account in each user profile.

| Step | User A | User B | Expected Result |
| --- | --- | --- | --- |
| 1 | Sign into Mira and connect Gmail in Worker integrations | Do not connect Gmail yet | User A connects successfully; User B has no Gmail connection |
| 2 | Ask "show my latest 3 unread emails from Gmail" | Ask the same prompt without connecting Gmail | User A sees only User A Gmail; User B gets an authorization/connection-required response |
| 3 | Keep User A logged in | Connect a different Gmail account for User B | User B connects successfully without seeing User A data |
| 4 | Ask for latest unread emails again | Ask for latest unread emails again | Each user sees only their own Gmail data |
| 5 | Create a Gmail draft in each account | Create a Gmail draft in each account | Draft appears only in the matching Gmail account |
| 6 | Disconnect/reconnect Gmail for User A | Refresh User B and run the Gmail prompt again | User B still cannot access User A Gmail |

Capture the thread URL, timestamp, signed-in Mira email, connected Gmail email, tool name, and screenshot for any failure. A safe failure is `403`, `auth required`, or `connection required`; an unsafe failure is any cross-user email result or successful tool call using the wrong Gmail account.

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
curl -fsS https://suna-backend-3teh.onrender.com/v1/debug/features
curl -I -fsS https://mira-frontend-d85v.onrender.com
```

## Launch Gate

Do not mark production launch-ready until these are green:

1. `SUPABASE_JWT_SECRET` is set in Render and matching production/staging CI secrets are available.
2. Authenticated full E2E flow passes against production or staging.
3. Composio two-user isolation test passes.
4. Google Slides, PDF, and PPTX exports work from a generated deck on the current Render URL.
5. Credits usage records raw cost, marked-up credit charge, and gross margin per action.
6. CI workflows target Mira Render URLs and the `mira-ai` repo/branch, not legacy Kortix endpoints.
7. The integration credential cleanup migration has been applied in Supabase SQL.
