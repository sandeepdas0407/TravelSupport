# Repo conventions for Claude Code (human and CI agents)

See `plans/architecture.md` for the full architecture. Summary of conventions:

## Structure
- `frontend/` — React + TS + Vite + Tailwind. Components in `src/components/`, one file per component. Types in `src/types/tripPlan.ts` mirror `backend/app/schemas.py` by hand; run `npm run codegen:types` against a running backend to check for drift.
- `backend/` — FastAPI app in `app/`, deployed via the Azure Functions ASGI wrapper in `function_app.py`. Each external API (Google Maps, Open-Meteo, Google Places, Anthropic) has its own module under `app/services/`; `app/services/trip_planner.py` is the only place that orchestrates them.
- `infra/` — Bicep only. Never hand-edit resources in the Azure Portal for anything under source control.

## Conventions
- Backend: type hints everywhere (`mypy` runs in CI), `ruff` for lint/format, `httpx.AsyncClient` for all outbound HTTP, upstream failures raise `UpstreamServiceError`/`SynthesisError` from `app/utils/errors.py` — geocoding/routing failures are fatal (400), weather/lodging failures degrade gracefully into `meta.warnings`.
- Frontend: `react-hook-form` + `zod` for form validation (must mirror backend Pydantic constraints), Tailwind utility classes (see the `.input` component class in `src/index.css` for form fields), no CSS-in-JS.
- Never commit secrets. `ANTHROPIC_API_KEY`, `GOOGLE_MAPS_API_KEY`, `GOOGLE_PLACES_API_KEY` are read from `.env` (backend) locally and from GitHub Actions secrets / Azure Static Web Apps app settings in CI/production.
- The `additional_info` free-text field is user-controlled and is treated as untrusted data inside the Claude synthesis prompt (delimited, never as instructions) — see `app/services/synthesis.py::_build_prompt`.

## CI agent personas (`.github/workflows/`)

This repo's CI/CD pipeline runs several pipeline stages as AI agents via `claude-code-action`, not just deterministic scripts. If you are one of these agents, your persona and boundaries are:

| Persona | Workflow | Can edit | Cannot do |
|---|---|---|---|
| design-reviewer | `agent-design-review.yml` | Nothing (read-only; `Edit`/`Write` explicitly disallowed) | Only post PR review comments |
| build-fix / test-fix | `pr-checks.yml` → `agent-ci-fix` job | `frontend/**`, `backend/**` only | Touch `.github/workflows/**`, `infra/**`, dotfiles, or secrets; force-push; exceed 3 fix iterations |
| deploy-verify | `deploy-and-verify.yml` | Nothing (read-only; `Edit`/`Write` explicitly disallowed) | Edit any source file; its only actions on failure are `git revert` or opening an incident issue |

Note: build-fix/test-fix runs as a same-workflow job (`needs: [frontend, backend]`, `if: failure()`) inside `pr-checks.yml` rather than a separate `workflow_run`-triggered file — this keeps it in the original `pull_request` event context, which is what `claude-code-action` needs to correctly auto-commit/push to the existing PR branch. Each fix attempt is a real commit + push, which re-triggers `pr-checks.yml`; the 3-attempt cap is read back from git history (`Agentic-Fix: true` commit trailers) on every run, so the loop is self-terminating without needing shared state between runs.

All agent stages have bounded iteration counts and `max_turns` enforced by the workflow itself, not by self-reported completion. Deterministic checks (`pr-checks.yml`, `infra-plan.yml`) always run first; agents only engage after a deterministic signal (a failure to fix, a merge to verify).
