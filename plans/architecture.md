# TravelSupport — Travel Planner App with Agentic CI/CD

## Context

The goal is a travel-planning web app: the user submits from/to locations, number of travel days, travel date, and free-text additional info, and the app returns a generated trip plan — accounting for season, weather, route, and destination — including recommended places to stay.

Beyond the app itself, the user wants the entire delivery pipeline (design → build → test → deploy) automated and run by **AI agents in agentic loops**, not just conventional CI/CD jobs. The natural fit, since this is being built from inside Claude Code, is Anthropic's official `claude-code-action` GitHub Action: headless Claude Code runs inside GitHub Actions, each pipeline stage given a distinct persona/prompt and scoped permissions, iterating (retry/fix) within bounded limits. Deployment target is Azure, source control is a single GitHub repo, pipeline is GitHub Actions.

This is a greenfield project (the working directory is currently empty) — this plan defines the initial architecture and build sequence from scratch, to be executed incrementally.

### Decisions made with the user up front
- **Pipeline**: AI agents (via `claude-code-action`) run the design/build/test/deploy stages in CI, with bounded iteration loops — not just themed conventional CI jobs.
- **Stack**: React frontend + Python FastAPI backend.
- **Data sources**: Open-Meteo (free, no key) for weather; Azure Maps for routing/geocoding; Google Places API for lodging/POI data. Anthropic Claude API (server-side) synthesizes all of it plus the user's free-text into the final narrative plan.
- **Persistence**: Stateless MVP — no login, no database.
- **Repo**: single monorepo (`frontend/`, `backend/`, `infra/`, `.github/workflows/`).
- **Azure hosting**: Azure Static Web Apps + managed Functions API (FastAPI wrapped via the Azure Functions ASGI adapter).

---

## 1. Repo Layout

```
TravelSupport/
├── frontend/                     # React + TS + Vite
│   ├── src/
│   │   ├── main.tsx, App.tsx
│   │   ├── api/tripPlanClient.ts         # typed fetch -> POST /api/trip-plan
│   │   ├── components/                    # TripRequestForm, TripPlanResult,
│   │   │                                  # RouteSummaryCard, WeatherForecastList,
│   │   │                                  # LodgingSuggestions, NarrativePlan
│   │   ├── hooks/useTripPlan.ts
│   │   └── types/tripPlan.ts             # generated from backend OpenAPI
│   ├── tests/                            # vitest + @testing-library/react
│   └── staticwebapp.config.json          # SPA fallback, /api/* routing, headers
│
├── backend/                       # == Azure SWA "api_location"
│   ├── function_app.py                   # Azure Functions ASGI entrypoint
│   ├── host.json, requirements.txt, pyproject.toml
│   ├── local.settings.json.example, .env.example
│   ├── app/
│   │   ├── main.py                       # FastAPI() instance, CORS, routers
│   │   ├── config.py                     # pydantic-settings (reads secrets)
│   │   ├── schemas.py                    # Pydantic request/response models
│   │   ├── routers/trip_plan.py, health.py
│   │   ├── services/
│   │   │   ├── routing.py                # Azure Maps geocode + route
│   │   │   ├── weather.py                # Open-Meteo forecast + climatology fallback
│   │   │   ├── places.py                 # Google Places (New) nearby search
│   │   │   ├── synthesis.py              # Claude Messages API call
│   │   │   └── trip_planner.py           # orchestrator
│   │   └── utils/dates.py, errors.py
│   └── tests/unit/, tests/integration/
│
├── infra/                         # Bicep IaC
│   ├── main.bicep
│   ├── modules/staticWebApp.bicep, appInsights.bicep, logAnalytics.bicep, azureMaps.bicep
│   ├── parameters/main.dev.bicepparam, main.prod.bicepparam
│   └── README.md                         # one-time OIDC bootstrap steps
│
├── .github/workflows/
│   ├── pr-checks.yml                     # deterministic lint/typecheck/test/build
│   ├── agent-design-review.yml           # design-reviewer agent (advisory, read-only)
│   ├── agent-ci-fix.yml                  # build-fix + test-fix agent loop
│   ├── infra-plan.yml                    # bicep what-if on infra/** PRs
│   ├── infra-apply.yml                   # manual, environment-gated apply
│   └── deploy-and-verify.yml             # deploy + deploy-verify agent
├── .github/CODEOWNERS
├── CLAUDE.md                             # repo conventions + CI agent persona docs
└── README.md
```

`backend/` doubles as the SWA API deployment unit: Azure Functions' Python V2 model needs `host.json`/`requirements.txt`/`function_app.py` at the deployment root, so those sit alongside the importable `app/` package rather than duplicating code into a separate folder.

---

## 2. Backend Design

**`POST /api/trip-plan`** — request: `from_location`, `to_location`, `start_date` (ISO date, not in the past), `num_days` (1–21), `additional_info` (optional, length-capped, treated as untrusted data in the Claude prompt — never as instructions, to guard against prompt injection).

Response bundles: `route` (origin/destination geocode + distance/duration from Azure Maps), `weather` (per-day; `source: "forecast"` within Open-Meteo's ~16-day horizon, `source: "climatology"` beyond it — clearly flagged, never silently presented as a live forecast), `lodging` (top Google Places lodging results near the destination), `narrative_plan` (Claude-generated summary + day-by-day + recommended stays + packing suggestions), and `meta` (data sources used, warnings).

`GET /api/health` — liveness check with no upstream calls, used by the deploy-verify agent.

Error handling: geocoding failure is fatal (400); weather/lodging upstream failures degrade gracefully with a `meta.warnings` note rather than failing the whole request; Anthropic failures return 502/504 after retry.

**Modules**: `services/routing.py`, `weather.py`, `places.py` each wrap one external API via `httpx.AsyncClient`; `services/synthesis.py` builds the Claude prompt and calls the Messages API with a forced JSON/tool schema for reliable structured output; `services/trip_planner.py` orchestrates (`asyncio.gather` the three data calls, then synthesize); `app/config.py` (pydantic-settings) reads `ANTHROPIC_API_KEY`, `AZURE_MAPS_SUBSCRIPTION_KEY`, `GOOGLE_PLACES_API_KEY` from env locally and from Azure Static Web Apps Application Settings in production — never exposed to the frontend.

**Azure Functions ASGI entrypoint** (`backend/function_app.py`):
```python
import azure.functions as func
from app.main import app as fastapi_app
app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)
```
This hosts the FastAPI app inside Azure Functions without rewriting routes as Functions handlers.

**Local dev**, three tiers depending on what's being validated: (1) `uvicorn app.main:app --reload` for fast iteration with Swagger UI, (2) `func start` (Azure Functions Core Tools) to validate the ASGI wrapper, (3) `swa start` (SWA CLI) to validate the full frontend+`/api/*` proxy exactly as production.

---

## 3. Frontend Design

React 18 + TypeScript + Vite + Tailwind. `TripRequestForm.tsx` (react-hook-form + zod, mirroring backend validation) submits via `useTripPlan.ts` (fetch wrapper with `idle/loading/success/error` state). `TripPlanResult.tsx` composes `RouteSummaryCard`, `WeatherForecastList` (visually flags climatology-estimated days), `LodgingSuggestions` (links to Google Maps), `NarrativePlan`. Types in `frontend/src/types/tripPlan.ts` are generated from the backend's OpenAPI schema via `openapi-typescript`, keeping frontend/backend contracts single-sourced. `staticwebapp.config.json` handles SPA fallback routing and security headers.

---

## 4. Agentic CI/CD Pipeline (GitHub Actions)

| Workflow | Trigger | Nature | Permissions | Exit condition |
|---|---|---|---|---|
| `pr-checks.yml` | PR → main | Deterministic (lint/typecheck/unit test/build) | `contents: read` | Pass/fail, single pass |
| `agent-design-review.yml` | PR opened/synchronize | **design-reviewer** agent: checks diff against architecture/conventions | Read-only tools; `pull-requests: write` for comments only; no Edit/Write | Single pass, advisory |
| `agent-ci-fix.yml` | `pr-checks.yml` fails | **build-fix** then **test-fix** agent | Edit/Write scoped to `frontend/**`/`backend/**` only (never workflows/infra/secrets); `contents: write` to push fix commits (no force-push) | Re-run checks after each fix; **max 3 iterations** (workflow-enforced counter); on exhaustion, fail + label `needs-human-review` |
| `infra-plan.yml` | PR touching `infra/**` | Deterministic (`bicep what-if`) | OIDC read-only role | Single pass, posts plan as PR comment |
| `infra-apply.yml` | Manual dispatch only | Deterministic, human-approval-gated | OIDC contributor role, GitHub Environment reviewers required | No auto-retry — deliberately not agentic given blast radius |
| `deploy-and-verify.yml` | Push to main | Deploy (deterministic) then **deploy-verify** agent | Verify agent: no Edit/Write; Bash limited to `curl`/App Insights queries/`gh issue create`/`git revert` | Health + smoke-test check; max 2 attempts; on failure, revert the merge commit or open an incident issue — never "fixes" production |

**Guardrails**: hard per-workflow iteration caps enforced by shell logic (not agent self-report); `max_turns` bounding each individual agent invocation; `timeout-minutes` wall-clock backstops; path-scoped Edit/Write allowlists per persona (agents can never modify `.github/workflows/**`, `infra/**`, or secrets to grant themselves more power); branch protection on `main` requires PR + green checks so no agent pushes directly to `main`; deploy job depends structurally on the test-agent job succeeding; Anthropic Console workspace spend limit as an org-level cost backstop; `concurrency` groups to cancel stale stacked agent runs.

`ANTHROPIC_API_KEY` is a GitHub Actions secret passed to every `claude-code-action` step. Azure access uses OIDC federated identity (no long-lived secret) — the one-time AAD app registration + federated credential bootstrap is a manual `az cli` step documented in `infra/README.md` (can't be created by Bicep itself). `AZURE_STATIC_WEB_APPS_API_TOKEN` is retrieved after first infra apply and stored as a secret for the deploy action.

---

## 5. Azure Resources (via `infra/` Bicep)

- **Azure Static Web Apps** (Free tier to start) — hosts frontend + managed Functions API together.
- **Log Analytics Workspace + Application Insights** — backend observability (`azure-monitor-opentelemetry`), connection string as an SWA app setting.
- **Azure Maps account** (Gen2 pricing) — geocoding + routing.
- *(deferred hardening)* Key Vault + managed identity for secrets, once past MVP.

`infra/main.bicep` composes the modules per environment via `.bicepparam` files. `infra-plan.yml` runs `what-if` on PRs; actual apply is only via manually-dispatched, environment-gated `infra-apply.yml` — intentionally kept out of the agentic loop.

---

## 6. Build Order

1. **M1** — Scaffold `frontend/` and `backend/`; verify `uvicorn` and `npm run dev` run independently with a working `/api/health`.
2. **M2** — Implement `routing.py`, `weather.py`, `places.py`, `synthesis.py`, `trip_planner.py` against real APIs with mocked unit tests (`respx`); `/api/trip-plan` fully functional locally.
3. **M3** — Build the frontend form + result components wired to the local backend; generate shared types.
4. **M4** — `pr-checks.yml` deterministic CI green for both frontend and backend, before adding any agentic layer.
5. **M5** — Add `agent-design-review.yml` and `agent-ci-fix.yml`; validate iteration caps and path-scoping against real failure scenarios.
6. **M6** — Author and manually apply `infra/` Bicep (after OIDC bootstrap); validate `function_app.py` via `func start`/`swa start`; wire `deploy-and-verify.yml`.
7. **M7** — End-to-end verification against the live SWA URL; confirm App Insights telemetry, cost/rate-limit guardrails (Anthropic spend limit, Google Places field-mask scoping).

Deterministic CI is deliberately green (M4) before agents are layered on top (M5), since the fix-loop agents need a reliable fast signal to iterate against.

---

## 7. Key Risks / Open Questions (carried forward, not blocking)

- Open-Meteo's ~16-day forecast horizon means far-future travel dates fall back to historical climatology — must stay clearly labeled end-to-end so users don't mistake it for a live forecast.
- Google Places API (New) is billed per request/field-mask tier — restrict `fieldMask` and result count to control cost.
- Azure Maps free-tier monthly transaction grants — each trip-plan request costs ~2 geocode + 1 route call; monitor as usage grows.
- `claude-code-action` cost scales with diff size and fix-loop iterations — mitigated via `if: failure()` gating, `max_turns` caps, and diff-scoped context.
- No auth/rate-limiting on the stateless MVP endpoint — a follow-up item (per-IP limiting or CAPTCHA) once real traffic is expected, since the endpoint fans out to three paid/rate-limited upstreams.
- OIDC federated-credential bootstrap is a one-time manual step outside IaC — must stay documented in `infra/README.md` so it isn't lost.

---

## Verification

- **M1–M3**: run `uvicorn app.main:app --reload` and `npm run dev` locally, exercise `POST /api/trip-plan` via the running frontend form end-to-end with real API keys in `.env`.
- **M4**: confirm `pr-checks.yml` runs and passes on a real PR (lint, typecheck, `pytest`, `vitest`, both builds).
- **M5**: intentionally introduce a failing test/lint error in a PR and confirm `agent-ci-fix.yml` detects it, patches within the iteration cap, and re-passes checks; confirm it refuses to touch out-of-scope paths.
- **M6–M7**: after `infra-apply.yml` and `deploy-and-verify.yml` run, hit the live SWA URL's `/api/health` and submit a real trip-plan request through the deployed frontend; check Application Insights for the request trace and confirm the deploy-verify agent's health/smoke checks passed.

---

## Addendum (2026-09-17): SWA managed Functions replaced with a linked standalone Function App

The original plan hosted the backend as Azure Static Web Apps' "managed Functions" (the
`api_location` input to `azure/static-web-apps-deploy-action`, built in-place by Oryx during the
SWA deploy). On first real deploy this consistently failed with a generic
`Deployment Failure Reason: Failed to deploy the Azure Functions` during Azure's server-side
polling phase, despite the Oryx build itself succeeding. This turned out to be an open,
platform-wide Azure bug affecting SWA managed-Functions deploys across multiple language runtimes
(.NET, Next.js, and — per this repo — Python), on both Free and Standard SKUs, unrelated to any
code in this repo. Tracking issues: [Azure/static-web-apps#1761](https://github.com/Azure/static-web-apps/issues/1761),
[#1760](https://github.com/Azure/static-web-apps/issues/1760).

**Fix**: the backend is now deployed as its own standalone Azure Function App resource
(`infra/modules/functionApp.bicep` — Linux Consumption plan + storage account + the same
`function_app.py` ASGI entrypoint, unchanged), and linked to the Static Web App via SWA's
[linked backends](https://learn.microsoft.com/azure/static-web-apps/apis-overview#bring-your-own-functions)
feature (`Microsoft.Web/staticSites/linkedBackends` in `infra/modules/staticWebApp.bicep`).
Requests to `/api/*` on the SWA's own domain are still transparently proxied to the Function App
— same origin from the frontend's perspective, so no CORS changes were needed. `deploy-and-verify.yml`
now has separate `deploy-frontend` (SWA, static content only) and `deploy-backend`
(`Azure/functions-action@v1`, direct Function App deploy) jobs instead of one combined step. This
sidesteps the broken managed-Functions path entirely and, per the linked issues, is also the more
commonly-recommended workaround in the community while Microsoft's fix is pending.
