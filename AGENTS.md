# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project purpose

- Azure Functions (Python) API that fills a Visio template and returns a generated `.vsdx`.
- Primary endpoint: `POST /api/fill-template` (implemented via catch-all router in `function_app.py`).

## Source of truth

- API entrypoint and routing: `function_app.py`
- Template fill logic: `pyscripts/fill_template.py`
- Infra/deployment: `azure.yaml` and `infra/`
- User-facing docs: `README.md`

## Non-negotiable behavior

- Keep response body as **binary** `.vsdx` bytes.
- Do **not** convert output to base64 unless explicitly requested.
- Keep `Content-Type` as `application/vnd.ms-visio.drawing`.
- Preserve response metadata headers:
  - `Content-Disposition`
  - `X-Tokens-Filled`
  - `X-Tokens-Zeroed`
  - `X-Lines-Scrubbed`

## Auth and security

- Current auth level is `FUNCTION` in `function_app.py`.
- Deployed requests require a function key (`?code=...` or `x-functions-key`).
- Do not switch to `ANONYMOUS` unless explicitly requested by the user.
- Never commit secrets, keys, connection strings, or `.env` secrets.

## Allowed changes

- Add/modify route handlers through the `ROUTES` map.
- Extend payload handling in a backward-compatible way.
- Improve error messages, logging, and docs.
- Add tests or test scripts if requested.

## Avoid unless requested

- Large refactors of routing architecture.
- Changing endpoint paths or response contract.
- Altering deployment topology/Bicep defaults.
- Broad formatting-only changes across unrelated files.

## Working style expectations

- Make minimal, targeted edits.
- Fix root causes instead of patching symptoms.
- Keep backward compatibility for existing clients.
- Update `README.md` when behavior or usage changes.

## Local validation workflow

1. Create/activate venv.
2. `pip install -r requirements.txt`
3. Start Azurite.
4. Start Functions host: `func start`
5. Send `POST /api/fill-template` with JSON payload.
6. Confirm:
   - HTTP 200
   - binary `.vsdx` output
   - expected headers present
   - unknown route/method returns 404

## Deployment notes

- Use `azd up` for provision + deploy.
- `azd provision --preview` may require an initialized/default `azd` environment.
- If deployed endpoint returns `401`, check function key usage first.

## Definition of done for feature work

- Code updated and consistent with existing style.
- Endpoint behavior verified locally (or blocker documented clearly).
- `README.md` updated when needed.
- No unrelated file churn.
