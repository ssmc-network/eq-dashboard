import io
import json
import zipfile

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from providers.json_status_provider import JsonStatusProvider
from schemas.layout import LayoutDefinition
from services.import_export_service import validate_layout_json, validate_status_json
from services.layout_service import (
    LayoutNotFoundError,
    get_layout,
    layout_exists,
    list_layouts,
    rename_layout,
    save_layout,
)

router = APIRouter(tags=["api"])

_provider = JsonStatusProvider()


@router.get("/standalone/layout/export")
async def export_layout(layout_id: str = Query(...)) -> JSONResponse:
    try:
        layout = get_layout(layout_id)
    except LayoutNotFoundError as exc:
        raise HTTPException(status_code=404, detail="layout not found") from exc
    return JSONResponse(
        content=layout.model_dump(by_alias=True, mode="json"),
        headers={"Content-Disposition": f'attachment; filename="{layout_id}-layout.json"'},
    )


@router.get("/standalone/layout/export/all")
async def export_all_layouts() -> Response:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for meta in list_layouts():
            layout = get_layout(meta.id)
            payload = json.dumps(layout.model_dump(by_alias=True, mode="json"), ensure_ascii=False, indent=2)
            zf.writestr(f"{meta.id}.json", payload)
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="all-layouts.zip"'},
    )


@router.get("/standalone/status/export")
async def export_status() -> JSONResponse:
    status = _provider.load_status()
    return JSONResponse(
        content=status.model_dump(by_alias=True, mode="json"),
        headers={"Content-Disposition": 'attachment; filename="status.json"'},
    )


@router.post("/layouts/save")
async def save_layout_endpoint(
    request: Request,
    original_id: str = Query(""),
    overwrite: bool = Query(False),
) -> JSONResponse:
    raw = await request.body()
    result = validate_layout_json(raw)
    if not result.ok:
        return JSONResponse(status_code=422, content={"ok": False, "errors": result.errors})

    layout = LayoutDefinition.model_validate(json.loads(raw))
    new_id = layout.layout.id
    is_rename = bool(original_id) and original_id != new_id

    if new_id != original_id and layout_exists(new_id) and not overwrite:
        existing = get_layout(new_id)
        return JSONResponse(
            status_code=409,
            content={"ok": False, "needsConfirmation": True, "existingName": existing.layout.name},
        )

    if is_rename:
        rename_layout(original_id, layout)
    else:
        save_layout(layout)
    return JSONResponse(content={"ok": True, "id": layout.layout.id, "name": layout.layout.name})


@router.post("/standalone/layout/import")
async def import_layout(file: UploadFile = File(...)) -> dict:
    result = validate_layout_json(await file.read())
    return {"valid": result.ok, "errors": result.errors, "summary": result.summary}


@router.post("/standalone/status/import")
async def import_status(file: UploadFile = File(...)) -> dict:
    result = validate_status_json(await file.read())
    return {"valid": result.ok, "errors": result.errors, "summary": result.summary}
