# Domain Cutover Checklist

Last updated: 2026-05-01

The current Render URLs are the controlled pre-domain production environment:

- Frontend: `https://mira-frontend-d85v.onrender.com`
- Backend: `https://suna-backend-3teh.onrender.com/v1`

When the final brand/domain is chosen, update these items in one controlled pass and re-run the full production smoke and auth/export/billing checks.

## Required DNS / Hosting

| Area | Update |
| --- | --- |
| Frontend domain | Add final app domain to the Render frontend service. |
| Backend/API domain | Decide whether API remains on Render subdomain or moves to `api.<domain>`. |
| TLS | Confirm Render-managed TLS is active for frontend and backend domains. |

## Backend Env

| Env var | Target value |
| --- | --- |
| `FRONTEND_URL` | `https://<final-app-domain>` |
| `BACKEND_URL` or `WEBHOOK_BASE_URL` | `https://<final-api-domain-or-render-backend>/v1` |
| `GOOGLE_REDIRECT_URI` | `https://<final-api-domain-or-render-backend>/v1/google/callback` |

## Frontend Env

| Env var | Target value |
| --- | --- |
| `NEXT_PUBLIC_URL` or `NEXT_PUBLIC_APP_URL` | `https://<final-app-domain>` |
| `NEXT_PUBLIC_BACKEND_URL` | `https://<final-api-domain-or-render-backend>/v1` |
| `NEXT_PUBLIC_ENV_MODE` | `production` |

## Supabase

| Setting | Target value |
| --- | --- |
| Site URL | `https://<final-app-domain>` |
| Redirect URLs | `https://<final-app-domain>/auth/callback` |
| Redirect URLs | Desktop deep-link callback if desktop remains supported. |

## Google Cloud OAuth

| Setting | Target value |
| --- | --- |
| Authorized JavaScript origins | `https://<final-app-domain>` |
| Authorized redirect URI | `https://<final-api-domain-or-render-backend>/v1/google/callback` |

Current temporary Google redirect URI:

```text
https://suna-backend-3teh.onrender.com/v1/google/callback
```

## Stripe

| Setting | Target value |
| --- | --- |
| Checkout success URL | `https://<final-app-domain>/...` |
| Checkout cancel URL | `https://<final-app-domain>/...` |
| Customer portal return URL | `https://<final-app-domain>/...` |
| Webhook endpoint | `https://<final-api-domain-or-render-backend>/v1/billing/webhook` or actual configured route |
| Branding | Final product name, icon, logo, support email, statement descriptor. |

## Email

| Setting | Target value |
| --- | --- |
| Sender domain | Verify final sending domain if transactional email is enabled. |
| SPF/DKIM/DMARC | Configure through the selected email provider. |
| Supabase email templates | Update links/copy to final domain and brand. |

## Final Verification

1. Run `scripts/production_smoke_check.sh`.
2. Sign in with Google and email magic link.
3. Create a thread and complete a short agent run.
4. Export one generated deck as PDF, PPTX, and Google Slides.
5. Run Composio Gmail isolation test.
6. Complete Stripe checkout in test mode or with an internal live test.
7. Confirm credit balance, usage attribution, and webhook idempotency.
