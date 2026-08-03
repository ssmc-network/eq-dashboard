from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

from providers.json_status_provider import JsonStatusProvider, LayoutFileNotFoundError
from services.import_export_service import validate_layout_json, validate_status_json
from services.layout_service import LayoutNotFoundError, get_layout

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


@router.get("/standalone/status/export")
async def export_status(layout_id: str = Query(...)) -> JSONResponse:
    try:
        status = _provider.load_status(layout_id)
    except LayoutFileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="status not found") from exc
    return JSONResponse(
        content=status.model_dump(by_alias=True, mode="json"),
        headers={"Content-Disposition": f'attachment; filename="{layout_id}-status.json"'},
    )


@router.post("/standalone/layout/import")
async def import_layout(file: UploadFile = File(...)) -> dict:
    result = validate_layout_json(await file.read())
    return {"valid": result.ok, "errors": result.errors, "summary": result.summary}


@router.post("/standalone/status/import")
async def import_status(file: UploadFile = File(...)) -> dict:
    result = validate_status_json(await file.read())
    return {"valid": result.ok, "errors": result.errors, "summary": result.summary}
