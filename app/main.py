from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.i18n import get_language, register_i18n_globals, translate
from core.log_modules import log_application
from routes import api, ui

app = FastAPI(title="EQ Dashboard")
templates = Jinja2Templates(directory="templates")
register_i18n_globals(templates)
logger = log_application(__name__)

HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(ui.router)
app.include_router(api.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _error_message(status_code: int, lang: str) -> str:
    if status_code == HTTP_NOT_FOUND:
        return translate("error.not_found", lang)
    if status_code >= HTTP_SERVER_ERROR:
        return translate("error.server_error", lang)
    return translate("error.generic", lang)


def _render_error(request: Request, status_code: int) -> Response:
    message = _error_message(status_code, get_language(request))
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(request, "partials/inline_error.html", {"message": message}, status_code=200)
    return templates.TemplateResponse(
        request, "pages/error.html", {"status_code": status_code, "message": message}, status_code=status_code
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> Response:
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return _render_error(request, exc.status_code)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> Response:
    logger.error("unhandled exception", exc_info=exc, extra={"argument": {"path": request.url.path}})
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=500, content={"detail": "internal server error"})
    return _render_error(request, 500)
