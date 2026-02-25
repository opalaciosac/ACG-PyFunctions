import azure.functions as func
import logging
from collections.abc import Callable

from pyscripts.fill_template import TEMPLATE_VSDX, fill_template_bytes

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

RouteHandler = Callable[[func.HttpRequest], func.HttpResponse]


def handle_fill_template(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON in request body", status_code=400)

    if not isinstance(req_body, dict):
        return func.HttpResponse("Request body must be a JSON object.", status_code=400)

    data = req_body.get("data", req_body)
    scrub = bool(req_body.get("scrub", True))
    output_name = req_body.get("outputName", "filled.vsdx")

    if not isinstance(data, dict):
        return func.HttpResponse("'data' must be a JSON object when provided.", status_code=400)

    if not TEMPLATE_VSDX.exists():
        logging.error("Template file not found: %s", TEMPLATE_VSDX)
        return func.HttpResponse("Template file was not found on the server.", status_code=500)

    try:
        result_bytes, summary = fill_template_bytes(
            data=data,
            template_bytes=TEMPLATE_VSDX.read_bytes(),
            scrub=scrub,
        )
    except Exception as exc:
        logging.exception("Error generating filled template: %s", exc)
        return func.HttpResponse("Failed to generate template output.", status_code=500)

    logging.info(
        "fill-template succeeded. tokens_filled=%s tokens_zeroed=%s lines_scrubbed=%s",
        len(summary["tokens_filled"]),
        len(summary["tokens_zeroed"]),
        summary["lines_scrubbed"],
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{output_name}"',
        "X-Tokens-Filled": str(len(summary["tokens_filled"])),
        "X-Tokens-Zeroed": str(len(summary["tokens_zeroed"])),
        "X-Lines-Scrubbed": str(summary["lines_scrubbed"]),
    }
    return func.HttpResponse(
        body=result_bytes,
        status_code=200,
        mimetype="application/vnd.ms-visio.drawing",
        headers=headers,
    )


ROUTES: dict[tuple[str, str], RouteHandler] = {
    ("POST", "fill-template"): handle_fill_template,
}


def _normalize_path(req: func.HttpRequest) -> str:
    path = (req.route_params.get("path") or "").strip("/")
    return path

@app.route(route="{*path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def http_router(req: func.HttpRequest) -> func.HttpResponse:
    method = req.method.upper()
    path = _normalize_path(req)
    logging.info("Dispatching request method=%s path=%s", method, path)

    handler = ROUTES.get((method, path))
    if handler is None:
        supported_routes = [f"{route_method} /{route_path}" for route_method, route_path in sorted(ROUTES)]
        return func.HttpResponse(
            f"Route not found for {method} /{path or ''}. Available routes: {', '.join(supported_routes)}",
            status_code=404,
        )

    return handler(req)
