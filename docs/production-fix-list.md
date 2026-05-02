# Mira Production Fix List

Last updated: 2026-05-02

This list converts the production test failures and blocked checks into concrete work. Priority meanings:

- `P0`: must fix before launch
- `P1`: should fix before launch or immediately after controlled beta
- `P2`: quality/scaling improvement

## P0 Fixes

| Status | Area | Fix | Owner Notes |
| --- | --- | --- | --- |
| Fixed | Live backend deploy drift | Deploy backend code that exposes `/v1/debug/config`; production smoke currently fails only on this endpoint. | Backend and frontend are live on `8b44113a`; production smoke now passes. |
| Fixed | Authenticated E2E | Load Supabase test secrets into CI and run `backend/tests/e2e/test_full_flow.py::test_complete_api_flow` against production/staging. | GitHub Actions production E2E run `25215423631` completed successfully after CI secrets were added. |
| In Progress | Composio tenant isolation | Add/run a two-user Gmail integration test proving User A cannot access User B's email/tools. | Added unit coverage and disabled unsafe unscoped profile recovery by default. Still run a live two-clean-account Gmail test before broad public launch. |
| Partially Fixed | Export flow | Verify generated decks export to PDF, PPTX, and Google Slides. Fix OAuth `invalid_client` and silent download failures. | Backend PDF/PPTX export proxy and frontend download handling are in place. Google OAuth production-domain cutover is deferred to the domain/OAuth pass. |
| Fixed | Billing unit economics | Verify every LLM/tool action records raw cost, credit charge, markup, account, thread, and provider/model metadata. | Unit economics metadata is recorded for token usage, and `TOKEN_PRICE_MULTIPLIER=2.0` enforces 100% markup. Focused pricing tests pass. |
| Fixed | CI endpoints | E2E workflow must target Mira/Render URLs, not legacy Kortix URLs. | `.github/workflows/e2e-api-tests.yml` uses Mira URL variables/defaults and manual dispatch is working with the updated PAT permissions. |

## P1 Fixes

| Status | Area | Fix | Owner Notes |
| --- | --- | --- | --- |
| Open | Frontend verification | Make frontend lint/typecheck complete reliably in CI and locally. | `apps/frontend/package.json` now uses `eslint .`, but local ESLint/TypeScript still hung in this sandbox. |
| Fixed | Test dependencies | Standardize local backend test setup with either `uv` or a documented venv install path. | `mise exec -- ... uv run pytest` now works locally with the repo-pinned toolchain. |
| Fixed | CI launch gate | Add smoke check to CI after deploy and fail deploy verification if `/debug/config` is unavailable. | `scripts/production_smoke_check.sh` and `.github/workflows/render-production-smoke.yml` now exist. Live backend deploy is fixed. |
| Fixed in Render | Auth hardening | Set `SUPABASE_JWT_SECRET` in Render and CI secrets. | Render backend now reports `/v1/debug/config` status `ok` with zero warnings. Still add this to GitHub Actions secrets for CI E2E. |
| Open | Runtime env inventory | Ensure Render env vars match `backend/.env.example` and `docs/configuration-inventory.md`. | The config endpoint should become the source of truth once live. |
| Deferred | Google/Drive auth | Verify OAuth clients, redirect URLs, scopes, and per-user token storage for Google Slides/Drive. | Deferred to the domain/OAuth cutover pass per launch sequencing. Current backend returns clear configuration errors instead of silent failure. |
| Fixed in Render | Stripe env completion | Add/confirm `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and the agreed launch tier price IDs in Render. | Launch tier/top-up price IDs plus `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` are set in Render. Production `/v1/debug/config` reports zero errors and zero warnings. |
| Fixed | Stripe catalog alignment | Align Stripe product descriptions/price IDs with agreed tiers. | Created new Stripe products/prices for Plus 1,000 credits, Pro 2,500 credits, Ultra 10,000 credits, plus top-ups. Render now points at these price IDs. |
| Open | Observability | Confirm logs/traces include account id, thread id, run id, provider, tool name, cost, and error class. | Needed for debugging agent failures and customer support. |
| In Progress | Rate limits | Add or verify rate limits for expensive agent, media, scrape, and integration endpoints. | Added Redis-backed `/agent/start` burst limiting with in-memory fallback. Media/scrape provider-specific limits remain a follow-up. |
| Fixed | Account deletion/data retention | Verify user deletion removes or anonymizes account data, files, and integration credentials. | Added database trigger cleanup for MCP/Composio credential profiles, legacy MCP credentials, and Google OAuth tokens when an account is deleted. |

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
| Composio credential isolation | Disabled unscoped encrypted-profile auto-recovery by default and added regression tests. |
| Billing idempotency | Credit purchases now use the Stripe payment intent as the credit ledger idempotency key. |
| Agent burst limits | Added Redis-backed `/agent/start` rate limiting with documented env defaults. |
| Account deletion cleanup | Added a Supabase trigger migration that deletes integration credentials and Google OAuth tokens on account deletion. |

## Next Execution Order

1. Deploy the P0/P1 backend hardening changes and apply the new Supabase migration.
2. Rerun production smoke and the GitHub Actions production E2E workflow.
3. Verify Stripe webhook endpoint `POST https://suna-backend-3teh.onrender.com/v1/billing/webhook` is registered in Stripe and replay one signed event.
4. Run two-user live Composio isolation before broadly promoting Gmail/Calendar/Drive integrations.
5. Complete the domain/OAuth cutover, then confirm Google OAuth endpoint returns an auth URL and verify Google Slides export.
