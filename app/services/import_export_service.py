import json
from dataclasses import dataclass, field

from pydantic import ValidationError

from schemas.layout import LayoutDefinition
from schemas.status import StatusSnapshot


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    summary: dict[str, object] | None = None


def validate_layout_json(raw: bytes) -> ValidationResult:
    data, error = _parse_json(raw)
    if error is not None:
        return ValidationResult(ok=False, errors=[error])

    try:
        layout = LayoutDefinition.model_validate(data)
    except ValidationError as exc:
        return ValidationResult(ok=False, errors=_format_errors(exc))

    return ValidationResult(
        ok=True,
        summary={
            "schemaVersion": layout.schema_version,
            "id": layout.layout.id,
            "name": layout.layout.name,
            "width": layout.layout.width,
            "height": layout.layout.height,
            "itemCount": len(layout.items),
        },
    )


def validate_status_json(raw: bytes) -> ValidationResult:
    data, error = _parse_json(raw)
    if error is not None:
        return ValidationResult(ok=False, errors=[error])

    try:
        status = StatusSnapshot.model_validate(data)
    except ValidationError as exc:
        return ValidationResult(ok=False, errors=_format_errors(exc))

    return ValidationResult(
        ok=True,
        summary={
            "schemaVersion": status.schema_version,
            "generatedAt": status.generated_at.isoformat(),
            "statusCount": len(status.statuses),
        },
    )


def _parse_json(raw: bytes) -> tuple[object, str | None]:
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        return None, f"JSONの解析に失敗しました: {exc}"


def _format_errors(exc: ValidationError) -> list[str]:
    messages = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"])
        messages.append(f"{loc}: {err['msg']}" if loc else err["msg"])
    return messages
