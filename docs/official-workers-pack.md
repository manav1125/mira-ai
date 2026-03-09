# Official Worker Pack

This pack adds five centrally managed specialist workers for all users in addition to Mira.

## Workers

| Worker | Role | Core outputs | Default knowledge seed |
| --- | --- | --- | --- |
| Research Strategist | Market and strategy research lead | Research briefs, competitor maps, ICP memos, decision notes | `research-strategist-playbook.md` |
| Growth Marketer | Messaging and experimentation partner | Campaign briefs, landing-page copy, experiment backlogs, launch plans | `growth-marketer-playbook.md` |
| Sales Copilot | Founder sales execution partner | Account briefs, outbound drafts, discovery agendas, follow-up notes | `sales-copilot-playbook.md` |
| Customer Success | Onboarding and support operations lead | Onboarding checklists, support macros, FAQ drafts, VOC summaries | `customer-success-playbook.md` |
| Finance & Ops | KPI and operating cadence partner | KPI packs, runway plans, SOPs, operating reviews | `finance-ops-playbook.md` |

## Behavior

- All five workers are installed automatically for new accounts.
- Existing accounts are backfilled during prewarm/login and can also be backfilled with `backend/core/utils/scripts/manage_official_workers.py`.
- Existing official workers are also synced against the latest central catalog, so prompt, tool, icon, and starter knowledge updates roll forward without deleting the worker.
- Official workers are centrally managed, so their names, prompts, and core tool sets are locked.
- Official workers do not count against paid-plan custom worker limits.
- Each worker receives starter knowledge-base files assigned directly to that worker.

## Source of Truth

- Worker catalog, prompts, tools, and knowledge seeds: `backend/core/config/official_worker_catalog.py`
- Installation/backfill service: `backend/core/utils/official_worker_service.py`
- Lazy ensure path: `backend/core/utils/ensure_official_workers.py`
- Bulk install script: `backend/core/utils/scripts/manage_official_workers.py`
