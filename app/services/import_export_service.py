import json
from dataclasses import dataclass, field

from pydantic import ValidationError

from core.i18n import DEFAULT_LANGUAGE, translate
from schemas.layout import LayoutDefinition
from schemas.status import StatusSnapshot


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    summary: dict[str, object] | None = None


def validate_layout_json(raw: bytes, lang: str = DEFAULT_LANGUAGE) -> ValidationResult:
    data, error = _parse_json(raw, lang)
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


def validate_status_json(raw: bytes, lang: str = DEFAULT_LANGUAGE) -> ValidationResult:
    data, error = _parse_json(raw, lang)
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


def _parse_json(raw: bytes, lang: str) -> tuple[object, str | None]:
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        return None, translate("import.json_parse_error", lang, error=exc)


def _format_errors(exc: ValidationError) -> list[str]:
    # ここのメッセージはPydanticのバリデータ(schemas/*.py)が生成したものであり、
    # 一部は日本語のValueErrorをそのまま含む(例: 重複tagId、空文字チェック)。
    # バリデータ自体はリクエストのlangを受け取れないため、このエラー文言は翻訳の対象外。
    messages = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"])
        messages.append(f"{loc}: {err['msg']}" if loc else err["msg"])
    return messages
