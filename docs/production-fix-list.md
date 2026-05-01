# Mira Production Fix List

Last updated: 2026-05-01

This list converts the production test failures and blocked checks into concrete work. Priority meanings:

- `P0`: must fix before launch
- `P1`: should fix before launch or immediately after controlled beta
- `P2`: quality/scaling improvement

## P0 Fixes

| Status | Area | Fix | Owner Notes |
| --- | --- | --- | --- |
| Fixed | Live backend deploy drift | Deploy backend code that exposes `/v1/debug/config`; production smoke currently fails only on this endpoint. | Backend and frontend are live on `8b44113a`; production smoke now passes. |
| Open | Authenticated E2E | Load Supabase test secrets into CI and run `backend/tests/e2e/test_full_flow.py::test_complete_api_flow` against production/staging. | Required secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, anon key. |
| Open | Composio tenant isolation | Add/run a two-user Gmail integration test proving User A cannot access User B's email/tools. | Temporary test account is `manavgupta1125@gmail.com`; replace with two clean test Gmail accounts before public launch. |
| Open | Export flow | Verify generated decks export to PDF, PPTX, and Google Slides. Fix OAuth `invalid_client` and silent download failures. | Google client config likely needs production OAuth client and redirect URLs. |
| Open | Billing unit economics | Verify every LLM/tool action records raw cost, credit charge, markup, account, thread, and provider/model metadata. | Needed to enforce the 100%+ margin pricing plan. |
| Partially Fixed | CI endpoints | E2E workflow must target Mira/Render URLs, not legacy Kortix URLs. | `.github/workflows/e2e-api-tests.yml` now uses Mira URL variables/defaults. |

## P1 Fixes

| Status | Area | Fix | Owner Notes |
| --- | --- | --- | --- |
| Open | Frontend verification | Make frontend lint/typecheck complete reliably in CI and locally. | `apps/frontend/package.json` now uses `eslint .`, but local ESLint/TypeScript still hung in this sandbox. |
| Open | Test dependencies | Standardize local backend test setup with either `uv` or a documented venv install path. | Current local shell lacks `pytest` and `uv`, so backend unit tests were blocked. |
| Fixed | CI launch gate | Add smoke check to CI after deploy and fail deploy verification if `/debug/config` is unavailable. | `scripts/production_smoke_check.sh` and `.github/workflows/render-production-smoke.yml` now exist. Live backend deploy is fixed. |
| Fixed in Render | Auth hardening | Set `SUPABASE_JWT_SECRET` in Render and CI secrets. | Render backend now reports `/v1/debug/config` status `ok` with zero warnings. Still add this to GitHub Actions secrets for CI E2E. |
| Open | Runtime env inventory | Ensure Render env vars match `backend/.env.example` and `docs/configuration-inventory.md`. | The config endpoint should become the source of truth once live. |
| In Progress | Google/Drive auth | Verify OAuth clients, redirect URLs, scopes, and per-user token storage for Google Slides/Drive. | Google OAuth env vars are set on Render with current redirect URI `https://suna-backend-3teh.onrender.com/v1/google/callback`; backend redeploy required/started. |
| Open | Stripe env completion | Add/confirm `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and the agreed launch tier price IDs in Render. | Current Render backend env list only shows `STRIPE_TIER_6_50_ID_PROD` and `STRIPE_TIER_25_200_ID_PROD`; no Stripe secret/webhook key is visible. |
| Open | Stripe catalog alignment | Align Stripe product descriptions/price IDs with agreed tiers. | App/backend use Plus 1,000 credits, Pro 2,500 credits, Ultra 10,000 credits; current Stripe product descriptions show Launch/Fly/Soar with 3,000/10,000/25,000 credits. |
| Open | Observability | Confirm logs/traces include account id, thread id, run id, provider, tool name, cost, and error class. | Needed for debugging agent failures and customer support. |
| Open | Rate limits | Add or verify rate limits for expensive agent, media, scrape, and integration endpoints. | Prevents a single user from burning provider credits. |
| Open | Account deletion/data retention | Verify user deletion removes or anonymizes account data, files, and integration credentials. | Required for production trust/compliance. |

## P2 Fixes

| Status | Area | Fix | Owner Notes |
| --- | --- | --- | --- |
| Open | Slide quality | Improve prompt/tool contract so researched content maps to the selected template framework instead of generic filler. | Important for perceived product quality. |
| Open | Template media | Replace placeholder template imagery with relevant generated/sourced images or remove placeholders. | Current decks can look templated even when they render. |
| Open | Research quality | Add source quality rules and citation checks for research/document outputs. | Helps avoid generic or stale output. |
| Open | Media failure UX | Provider failures should show actionable messages and next steps, not generic apologies. | Especially useful for Daytona/Replicate/OpenRouter incidents. |

## Completed In Repo

| Area | Change |
| --- | --- |
| Testing plan | Added `docs/production-testing-plan.md` with launch smoke, integration, billing, and quality checks. |
| Smoke script | Added `scripts/production_smoke_check.sh` for repeatable live smoke testing. |
| CI endpoint drift | Updated `.github/workflows/e2e-api-tests.yml` to use Mira/Render URL variables instead of legacy Kortix URLs. |
| CI runtime config gate | Added `/debug/config` verification to the E2E workflow before authenticated tests run. |
| CI E2E target | Default E2E workflow now runs the full authenticated API flow instead of only sparse `tests/api` files. |
| Render smoke workflow | Added `.github/workflows/render-production-smoke.yml` for hourly/manual live Render checks. |
| Frontend lint script | Replaced `next lint` with direct `eslint .` in `apps/frontend/package.json`. |

## Next Execution Order

1. Confirm Google OAuth endpoint returns an auth URL and verify Google Slides export.
2. Add/confirm production Stripe secret and webhook secret in Render.
3. Align Stripe product descriptions/price IDs with agreed credit tiers: 1,000 / 2,500 / 10,000.
4. Add `PRODUCTION_SUPABASE_JWT_SECRET` to GitHub Actions secrets for CI E2E.
5. Load/confirm the rest of the Supabase test secrets in CI and run the full authenticated E2E flow.
6. Run two-user Composio isolation before allowing Gmail/Calendar/Drive integrations in production.
7. Verify billing/cost attribution on real agent runs before accepting paid users.
