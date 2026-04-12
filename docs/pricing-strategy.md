# Pricing Strategy For Launch

## Goal

Price Mira as a hybrid of:

- a monthly SaaS subscription for access, seats, agents, and workflow limits
- included monthly credits that absorb normal usage
- optional top-ups for heavy usage

This keeps pricing simple for customers while preserving margin as different agents, models, and tools consume very different amounts of provider spend.

## What The Platform Already Has

- Token-based billing for LLM usage
- Media billing for image and video generation
- Voice billing hooks for Vapi calls
- Credit balances, monthly grants, daily grants, and top-up purchases
- Subscription tiers and top-up price IDs

## What Was Missing

Before this change, the system could deduct credits but it was much harder to answer:

- which agent types are expensive
- which models are driving cost
- how much of a run is provider cost vs platform markup
- which workflows are margin-positive vs margin-negative

## New Unit Economics Layer

The billing pipeline now stores richer metadata on usage deductions, including:

- model
- prompt, completion, and cache token counts
- billed credit value in USD
- estimated provider cost in USD
- markup multiplier
- source runtime
- agent and run attribution when available

Admin reporting is exposed at:

- `GET /v1/admin/billing/unit-economics`

This endpoint shows:

- total billed usage value vs estimated provider cost
- margin capture
- breakdown by model
- breakdown by agent
- breakdown by runtime source

## Recommended Commercial Model

### 1. Keep subscription + credits

Use monthly plans as the default commercial motion:

- `Basic`: free or low-cost onboarding
- `Plus`: individual power users
- `Pro`: frequent operator / founder / analyst usage
- `Ultra` or `Team`: heavy usage, many concurrent runs, more triggers and workers

### 2. Treat credits as compute budget, not arbitrary points

Internally:

- `1 credit = $0.01 billed usage value`

That matches the current code path well because balances are stored in dollar-equivalent units and surfaced as credits at `100 credits per $1`.

### 3. Price plans from expected gross margin, not model list alone

For each tier:

1. Estimate the target monthly provider cost per active account.
2. Add infrastructure/tool overhead.
3. Add target gross margin.
4. Convert the result into included credits.

Use this formula:

`included_credit_value_usd <= target_monthly_price * target_usage_ratio`

Suggested starting guardrails:

- target markup on variable LLM cost: `100%` (`2.0x` billed value vs estimated provider cost)
- target gross margin: `70%+` on blended subscription revenue
- target included-credit utilization: `50% to 70%` of paid seats
- top-up gross margin: `20% to 40%`

### 4. Price top-ups at or above billed credit value

For launch, keep top-ups simple:

- `$10 = 1,000 credits`
- `$25 = 2,500 credits`
- `$50 = 5,000 credits`
- `$100 = 10,000 credits`

If you want stronger SaaS economics:

- keep subscription credits slightly discounted
- keep top-ups at full price

That makes subscriptions feel like the best value while preventing heavy users from becoming unprofitable.

### 5. Use limits as a second pricing lever

Do not rely only on credits. Keep tier differentiation in:

- concurrent runs
- number of custom workers
- scheduled triggers
- app triggers
- premium model availability

This improves monetization without forcing every price increase through token math.

## Recommended Launch Process

### Phase 1: Observe

For 2 to 4 weeks before broad production launch:

- track unit economics weekly
- identify top 10 costly models
- identify top 10 costly agents
- measure free-tier and paid-tier average provider cost per active account

### Phase 2: Calibrate

Adjust:

- included credits per tier
- which models are allowed on each tier
- top-up pricing
- concurrency and trigger limits

### Phase 3: Production Guardrails

Before broad launch, add:

- alert when any tier goes below target gross margin
- alert when any single account exceeds a defined monthly cost threshold
- alert when any agent template has poor margin

## Recommended Product Rules

- Show users remaining credits clearly
- Estimate expensive actions before they run
- Let users buy top-ups without changing plan
- Warn before high-cost tools or long-running media tasks
- Keep refunds automatic for platform failures

## What To Build Next

### High priority

- Customer-facing per-thread and per-project cost estimates
- Usage forecasting by tier
- Margin alerting for admins
- Separate reporting for included credits vs purchased top-ups

### Medium priority

- Per-tool unit economics
- Per-goal / workflow cost estimates before execution
- Model routing based on profitability targets

## Initial Pricing Recommendation

The agreed launch configuration is:

- `Basic`: free tier with weekly credits only
- `Plus ($20)`: `1,000` monthly credits
- `Pro ($50)`: `2,500` monthly credits
- `Ultra ($200)`: `10,000` monthly credits

These included credits should be treated as the usage budget bundled into the subscription. The subscription fee itself needs to cover Stripe, infrastructure, marketing, support, and platform margin separately from compute markup.
