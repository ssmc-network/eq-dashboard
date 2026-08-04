import json

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from schemas.layout import LayoutDefinition, LayoutMeta
from schemas.status import StatusSnapshot
from schemas.tag_mapping import TagMapping
from services.import_export_service import validate_layout_json, validate_status_json
from services.layout_service import LayoutNotFoundError, get_layout, layout_exists, list_layouts, save_layout
from services.status_service import get_dashboard, save_status
from services.tag_mapping_service import (
    TagMappingExistsError,
    TagMappingNotFoundError,
    create_tag_mapping,
    delete_tag_mapping,
    get_tag_mapping,
    list_tag_mappings,
    update_tag_mapping,
)

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="templates")

DEFAULT_LAYOUT_ID = "line-a"
DEFAULT_REFRESH_INTERVAL_SEC = 10
THEME_CHOICES = ("system", "light", "dark")
OPERATION_MODE_CHOICES = ("online", "offline")
SETTINGS_COOKIE_MAX_AGE = 60 * 60 * 24 * 365


@router.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/ui/dashboard")


@router.get("/ui/dashboard")
async def dashboard_default(request: Request) -> RedirectResponse:
    valid_ids = {meta.id for meta in list_layouts()}
    layout_id = request.cookies.get("default_layout_id")
    if layout_id not in valid_ids:
        layout_id = DEFAULT_LAYOUT_ID
    return RedirectResponse(url=f"/ui/dashboard/{layout_id}")


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
            "default_refresh_interval": _get_default_refresh_interval(request),
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
    return templates.TemplateResponse(
        request,
        "pages/api_settings.html",
        {"operation_mode": _get_operation_mode(request)},
    )


@router.get("/ui/tag-mappings", response_class=HTMLResponse)
async def tag_mappings(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "pages/tag_mappings.html",
        {"mappings": list_tag_mappings(), "editing": False, "mapping": None},
    )


@router.get("/ui/tag-mappings/new", response_class=HTMLResponse)
async def tag_mapping_new_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "partials/tag_mapping_form.html",
        {"editing": False, "mapping": None},
    )


@router.get("/ui/tag-mappings/{tag_id}/edit", response_class=HTMLResponse)
async def tag_mapping_edit_form(request: Request, tag_id: str) -> HTMLResponse:
    mapping = get_tag_mapping(tag_id)
    if mapping is None:
        raise HTTPException(status_code=404, detail="tag mapping not found")
    return templates.TemplateResponse(
        request,
        "partials/tag_mapping_form.html",
        {"editing": True, "mapping": mapping},
    )


@router.post("/ui/tag-mappings", response_class=HTMLResponse)
async def tag_mapping_create(
    request: Request,
    tag_id: str = Form(...),
    api_field: str = Form(...),
    running_value: str = Form(""),
    stopped_value: str = Form(""),
    alarm_value: str = Form(""),
) -> HTMLResponse:
    mapping = TagMapping(
        tagId=tag_id,
        apiField=api_field,
        runningValue=running_value,
        stoppedValue=stopped_value,
        alarmValue=alarm_value,
    )
    try:
        create_tag_mapping(mapping)
    except TagMappingExistsError:
        return templates.TemplateResponse(
            request,
            "partials/tag_mapping_form.html",
            {
                "editing": False,
                "mapping": mapping,
                "error": f"tagId「{tag_id}」は既に登録されています。",
            },
        )
    return _tag_mapping_saved_response(request)


@router.post("/ui/tag-mappings/{tag_id}", response_class=HTMLResponse)
async def tag_mapping_update(
    request: Request,
    tag_id: str,
    api_field: str = Form(...),
    running_value: str = Form(""),
    stopped_value: str = Form(""),
    alarm_value: str = Form(""),
) -> HTMLResponse:
    mapping = TagMapping(
        tagId=tag_id,
        apiField=api_field,
        runningValue=running_value,
        stoppedValue=stopped_value,
        alarmValue=alarm_value,
    )
    try:
        update_tag_mapping(tag_id, mapping)
    except TagMappingNotFoundError as exc:
        raise HTTPException(status_code=404, detail="tag mapping not found") from exc
    return _tag_mapping_saved_response(request)


@router.delete("/ui/tag-mappings/{tag_id}", response_class=HTMLResponse)
async def tag_mapping_delete(request: Request, tag_id: str) -> HTMLResponse:
    delete_tag_mapping(tag_id)
    return templates.TemplateResponse(
        request,
        "partials/tag_mapping_table.html",
        {"mappings": list_tag_mappings(), "oob": False},
    )


@router.get("/ui/standalone", response_class=HTMLResponse)
async def standalone(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "pages/standalone.html",
        {
            "available_layouts": list_layouts(),
            "operation_mode": _get_operation_mode(request),
        },
    )


@router.post("/ui/standalone/layout/import", response_class=HTMLResponse)
async def standalone_import_layout(request: Request, file: UploadFile = File(...)) -> HTMLResponse:
    raw = await file.read()
    result = validate_layout_json(raw)
    exists = bool(result.ok and result.summary and layout_exists(result.summary["id"]))
    return templates.TemplateResponse(
        request,
        "partials/import_result.html",
        {
            "result": result,
            "kind": "レイアウト",
            "filename": file.filename,
            "raw_json": raw.decode("utf-8") if result.ok else None,
            "exists": exists,
            "confirm_url": "/ui/standalone/layout/import/confirm",
        },
    )


@router.post("/ui/standalone/layout/import/confirm", response_class=HTMLResponse)
async def standalone_import_layout_confirm(request: Request, raw_json: str = Form(...)) -> HTMLResponse:
    result = validate_layout_json(raw_json.encode("utf-8"))
    if not result.ok:
        return templates.TemplateResponse(
            request,
            "partials/import_result.html",
            {"result": result, "kind": "レイアウト", "filename": "(保存時の再検証)"},
        )

    layout = LayoutDefinition.model_validate(json.loads(raw_json))
    was_existing = layout_exists(layout.layout.id)
    save_layout(layout)
    return templates.TemplateResponse(
        request,
        "partials/import_result.html",
        {"saved": True, "layout": layout, "was_existing": was_existing},
    )


@router.post("/ui/standalone/status/import", response_class=HTMLResponse)
async def standalone_import_status(request: Request, file: UploadFile = File(...)) -> HTMLResponse:
    raw = await file.read()
    result = validate_status_json(raw)
    return templates.TemplateResponse(
        request,
        "partials/import_result.html",
        {
            "result": result,
            "kind": "状態",
            "filename": file.filename,
            "raw_json": raw.decode("utf-8") if result.ok else None,
            "confirm_url": "/ui/standalone/status/import/confirm",
        },
    )


@router.post("/ui/standalone/status/import/confirm", response_class=HTMLResponse)
async def standalone_import_status_confirm(request: Request, raw_json: str = Form(...)) -> HTMLResponse:
    result = validate_status_json(raw_json.encode("utf-8"))
    if not result.ok:
        return templates.TemplateResponse(
            request,
            "partials/import_result.html",
            {"result": result, "kind": "状態", "filename": "(保存時の再検証)"},
        )

    status = StatusSnapshot.model_validate(json.loads(raw_json))
    save_status(status)
    return templates.TemplateResponse(
        request,
        "partials/import_result.html",
        {"saved": True, "status": status},
    )


@router.get("/ui/settings", response_class=HTMLResponse)
async def settings(request: Request) -> HTMLResponse:
    layouts = list_layouts()
    valid_ids = {meta.id for meta in layouts}
    default_layout_id = request.cookies.get("default_layout_id")
    if default_layout_id not in valid_ids:
        default_layout_id = DEFAULT_LAYOUT_ID

    return templates.TemplateResponse(
        request,
        "pages/settings.html",
        {
            "theme": _get_theme(request),
            "operation_mode": _get_operation_mode(request),
            "available_layouts": layouts,
            "default_layout_id": default_layout_id,
            "default_refresh_interval": _get_default_refresh_interval(request),
        },
    )


@router.post("/ui/settings")
async def save_settings(
    theme: str = Form("system"),
    operation_mode: str = Form("offline"),
    default_layout_id: str = Form(DEFAULT_LAYOUT_ID),
    default_refresh_interval: int = Form(DEFAULT_REFRESH_INTERVAL_SEC),
) -> RedirectResponse:
    if theme not in THEME_CHOICES:
        theme = "system"

    if operation_mode not in OPERATION_MODE_CHOICES:
        operation_mode = "offline"

    valid_ids = {meta.id for meta in list_layouts()}
    if default_layout_id not in valid_ids:
        default_layout_id = DEFAULT_LAYOUT_ID

    if default_refresh_interval < 1:
        default_refresh_interval = DEFAULT_REFRESH_INTERVAL_SEC

    response = RedirectResponse(url="/ui/settings", status_code=303)
    response.set_cookie("theme", theme, max_age=SETTINGS_COOKIE_MAX_AGE, samesite="lax")
    response.set_cookie("operation_mode", operation_mode, max_age=SETTINGS_COOKIE_MAX_AGE, samesite="lax")
    response.set_cookie("default_layout_id", default_layout_id, max_age=SETTINGS_COOKIE_MAX_AGE, samesite="lax")
    response.set_cookie(
        "default_refresh_interval",
        str(default_refresh_interval),
        max_age=SETTINGS_COOKIE_MAX_AGE,
        samesite="lax",
    )
    return response


def _tag_mapping_saved_response(request: Request) -> HTMLResponse:
    form_html = templates.env.get_template("partials/tag_mapping_form.html").render(
        {"request": request, "editing": False, "mapping": None}
    )
    table_html = templates.env.get_template("partials/tag_mapping_table.html").render(
        {"request": request, "mappings": list_tag_mappings(), "oob": True}
    )
    return HTMLResponse(content=form_html + table_html)


def _load_dashboard(layout_id: str):
    try:
        return get_dashboard(layout_id)
    except LayoutNotFoundError as exc:
        raise HTTPException(status_code=404, detail="layout not found") from exc


def _serialize_layout(layout: LayoutDefinition) -> str:
    return json.dumps(layout.model_dump(by_alias=True), ensure_ascii=False).replace("</", "<\\/")


def _get_theme(request: Request) -> str:
    theme = request.cookies.get("theme", "system")
    return theme if theme in THEME_CHOICES else "system"


def _get_operation_mode(request: Request) -> str:
    mode = request.cookies.get("operation_mode", "offline")
    return mode if mode in OPERATION_MODE_CHOICES else "offline"


def _get_default_refresh_interval(request: Request) -> int:
    raw = request.cookies.get("default_refresh_interval")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_REFRESH_INTERVAL_SEC
    return value if value >= 1 else DEFAULT_REFRESH_INTERVAL_SEC
