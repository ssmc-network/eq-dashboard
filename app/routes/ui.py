import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from schemas.layout import LayoutDefinition, LayoutMeta
from services.layout_service import LayoutNotFoundError, get_layout, list_layouts
from services.status_service import get_dashboard

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="templates")

DEFAULT_LAYOUT_ID = "line-a"
DEFAULT_REFRESH_INTERVAL_SEC = 10


@router.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/ui/dashboard")


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
async def layouts_list(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "pages/layouts_list.html",
        {"layouts": list_layouts()},
    )


@router.get("/ui/layouts/new", response_class=HTMLResponse)
async def layout_editor_new(request: Request) -> HTMLResponse:
    blank = LayoutDefinition(
        schemaVersion="1.0",
        layout=LayoutMeta(id="", name="", width=900, height=420),
        items=[],
    )
    return templates.TemplateResponse(
        request,
        "pages/layout_editor.html",
        {
            "layout": blank,
            "is_new": True,
            "initial_layout_json": _serialize_layout(blank),
        },
    )


@router.get("/ui/layouts/{layout_id}/edit", response_class=HTMLResponse)
async def layout_editor_edit(request: Request, layout_id: str) -> HTMLResponse:
    try:
        layout = get_layout(layout_id)
    except LayoutNotFoundError as exc:
        raise HTTPException(status_code=404, detail="layout not found") from exc
    return templates.TemplateResponse(
        request,
        "pages/layout_editor.html",
        {
            "layout": layout,
            "is_new": False,
            "initial_layout_json": _serialize_layout(layout),
        },
    )


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


def _load_dashboard(layout_id: str):
    try:
        return get_dashboard(layout_id)
    except LayoutNotFoundError as exc:
        raise HTTPException(status_code=404, detail="layout not found") from exc


def _serialize_layout(layout: LayoutDefinition) -> str:
    return json.dumps(layout.model_dump(by_alias=True), ensure_ascii=False).replace("</", "<\\/")
