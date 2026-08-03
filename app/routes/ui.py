from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from schemas.layout import LayoutDefinition
from services.status_service import DashboardBox, LayoutNotFoundError, get_dashboard, list_layouts

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="templates")

DEFAULT_LAYOUT_ID = "line-a"
DEFAULT_REFRESH_INTERVAL_SEC = 10


@router.get("/", response_class=HTMLResponse)
async def welcome(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/welcome.html", {})


@router.get("/ui/dashboard")
async def dashboard_default() -> RedirectResponse:
    return RedirectResponse(url=f"/ui/dashboard/{DEFAULT_LAYOUT_ID}")


@router.get("/ui/dashboard/{layout_id}", response_class=HTMLResponse)
async def dashboard(request: Request, layout_id: str) -> HTMLResponse:
    layout, boxes = _load_dashboard(layout_id)
    return templates.TemplateResponse(
        request,
        "pages/dashboard.html",
        {
            "layout": layout,
            "boxes": boxes,
            "available_layouts": list_layouts(),
            "default_refresh_interval": DEFAULT_REFRESH_INTERVAL_SEC,
        },
    )


@router.get("/ui/dashboard/{layout_id}/items", response_class=HTMLResponse)
async def dashboard_items(request: Request, layout_id: str) -> HTMLResponse:
    layout, boxes = _load_dashboard(layout_id)
    return templates.TemplateResponse(
        request,
        "partials/dashboard_items.html",
        {"layout": layout, "boxes": boxes},
    )


@router.get("/ui/layouts", response_class=HTMLResponse)
async def layouts(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/layout_editor.html", {})


@router.get("/ui/api-sources", response_class=HTMLResponse)
async def api_sources(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/api_settings.html", {})


@router.get("/ui/tag-mappings", response_class=HTMLResponse)
async def tag_mappings(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/tag_mappings.html", {})


@router.get("/ui/standalone", response_class=HTMLResponse)
async def standalone(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/standalone.html", {})


@router.get("/ui/settings", response_class=HTMLResponse)
async def settings(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/settings.html", {})


def _load_dashboard(layout_id: str) -> tuple[LayoutDefinition, list[DashboardBox]]:
    try:
        return get_dashboard(layout_id)
    except LayoutNotFoundError as exc:
        raise HTTPException(status_code=404, detail="layout not found") from exc
