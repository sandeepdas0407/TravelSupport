# TravelSupport

A travel-planning app: submit a from/to location, travel date, number of days, and optional notes, and get back a route summary, day-by-day weather, lodging suggestions, and an AI-generated trip plan.

- **Frontend**: React + TypeScript + Vite + Tailwind (`frontend/`)
- **Backend**: FastAPI, deployed on Azure Functions via the ASGI adapter (`backend/`)
- **Data sources**: Azure Maps (routing/geocoding), Open-Meteo (weather, with historical-climatology fallback beyond the forecast horizon), Google Places API (lodging), Anthropic Claude (trip synthesis)
- **Infra**: Azure Static Web Apps + Azure Maps + Application Insights, provisioned via Bicep (`infra/`)
- **CI/CD**: GitHub Actions, with design/build-fix/test-fix/deploy-verify stages run by AI agents (`claude-code-action`) alongside deterministic checks (`.github/workflows/`)

See `plans/architecture.md` for the full design and rationale.

## Local development

### Backend

```
cd backend
python -m venv .venv
source .venv/Scripts/activate   # or .venv/bin/activate on macOS/Linux
pip install -r requirements-dev.txt
cp .env.example .env            # fill in ANTHROPIC_API_KEY, AZURE_MAPS_SUBSCRIPTION_KEY, GOOGLE_PLACES_API_KEY
uvicorn app.main:app --reload --port 8000
```

Runs at `http://localhost:8000`, with interactive docs at `/docs`.

Tests: `pytest` · Lint: `ruff check .` · Types: `mypy app`

### Frontend

```
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173` and proxies `/api/*` to `http://localhost:8000` (see `vite.config.ts`).

Tests: `npm test` · Lint: `npm run lint` · Types: `npm run typecheck`

### Full Azure Static Web Apps emulation (optional)

Once both apps run standalone, validate the production routing/proxy with the [SWA CLI](https://azure.github.io/static-web-apps-cli/):

```
swa start http://localhost:5173 --api-location backend --run "npm run dev" --app-location frontend
```

## Required secrets / API keys

| Key | Where to get it | Used for |
|---|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com | Runtime trip-plan synthesis + CI agents (`claude-code-action`) |
| `AZURE_MAPS_SUBSCRIPTION_KEY` | Azure Portal → Azure Maps account | Geocoding + routing |
| `GOOGLE_PLACES_API_KEY` | Google Cloud Console → Places API (New) | Lodging suggestions |

None of these are required to run the frontend or backend test suites (all upstream calls are mocked in tests).
