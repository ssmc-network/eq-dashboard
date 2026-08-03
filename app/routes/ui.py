from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def welcome(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/welcome.html", {})


@router.get("/ui/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/dashboard.html", {})


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
