# ACG PyFunctions – Visio Template Generator

This project is an Azure Functions (Python) HTTP API that fills a Visio template (`.vsdx`) with JSON data and returns the generated file as a binary download.

It is designed to run locally with Azure Functions Core Tools and deploy with Azure Developer CLI (`azd`).

## What this API does

- Accepts a `POST` request at `/api/fill-template`.
- Replaces bracketed tokens in the Visio template using request JSON.
- Optionally scrubs empty visual lines after substitution.
- Returns a generated `.vsdx` file as **binary** (not base64).

## Current route map

Routing is implemented in [function_app.py](function_app.py) using a catch-all route and a route table.

- `POST /fill-template` → generate filled Visio file

To add a new endpoint, register another handler in the `ROUTES` dictionary in [function_app.py](function_app.py).

## Prerequisites

- Python 3.11
- Azure Functions Core Tools v4
- Azurite (local storage emulator)
- Azure Developer CLI (`azd`)
- (Optional) Visual Studio Code + Azure Functions extension

## Local setup

### 1) Create and activate a virtual environment

PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Start Azurite (separate terminal)

```powershell
azurite
```

### 4) Start the Functions host

```powershell
func start
```

## Test locally

You can use [test.http](test.http) or `curl`.

### Sample payload

```json
{
  "data": {
    "Client1FullName": "John A. Smith",
    "Client1ShortName": "John",
    "Client2FullName": "Jane B. Smith",
    "Client2ShortName": "Jane",
    "Year": "2026"
  },
  "scrub": true,
  "outputName": "estate-plan-sample.vsdx"
}
```

### `curl` example (saves file)

```bash
curl -X POST "http://localhost:7071/api/fill-template" \
  -H "Content-Type: application/json" \
  -d @payload.json \
  --output result.vsdx
```

## Response contract

On success:

- Status: `200 OK`
- Body: binary `.vsdx` bytes
- Content-Type: `application/vnd.ms-visio.drawing`
- Content-Disposition: attachment with output filename
- Metadata headers:
  - `X-Tokens-Filled`
  - `X-Tokens-Zeroed`
  - `X-Lines-Scrubbed`

Common errors:

- `400` invalid JSON or invalid `data` shape
- `404` route/method not registered
- `500` template file missing or generation failure

## Deploy to Azure

From the project root:

```powershell
azd up
```

This provisions infra and deploys the function app.

## Call the deployed endpoint

This app currently uses **Function-level auth** (`AuthLevel.FUNCTION`) in [function_app.py](function_app.py), so deployed calls require a function key.

### Request URL pattern

```text
https://<your-function-app>.azurewebsites.net/api/fill-template?code=<FUNCTION_KEY>
```

Or send key in header:

```text
x-functions-key: <FUNCTION_KEY>
```

### Get the function key

Azure CLI:

```powershell
az functionapp function keys list \
  --resource-group <resource-group> \
  --name <function-app-name> \
  --function-name http_router
```

Portal:

1. Open Function App
2. Go to **Functions** → `http_router`
3. Open **Function Keys**

## Notes for maintainers

- Template source path is managed in [pyscripts/fill_template.py](pyscripts/fill_template.py).
- API generation logic delegates to `fill_template_bytes(...)`.
- Keep responses binary for file-download clients; do not convert output to base64 unless client requirements change.

## Troubleshooting

- `401 Unauthorized` on Azure: missing or invalid function key.
- `Port 7071 is unavailable`: another local host is already using that port.
- `Template file was not found on the server`: verify template asset is included in deployment package.

## Cleanup

To remove provisioned Azure resources:

```powershell
azd down
```
