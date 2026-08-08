from dataclasses import dataclass, field

import httpx

from core.i18n import DEFAULT_LANGUAGE, translate
from core.log_modules import log_application
from schemas.api_config import ApiConfig
from services.api_test_service import TIMEOUT_SECONDS, build_auth_headers

MAX_FIELDS = 200

logger = log_application(__name__)


@dataclass
class DiscoveredField:
    path: str
    value: str


@dataclass
class DiscoverFieldsResult:
    ok: bool
    message: str = ""
    fields: list[DiscoveredField] = field(default_factory=list)
    truncated: bool = False


async def discover_fields(config: ApiConfig, lang: str = DEFAULT_LANGUAGE) -> DiscoverFieldsResult:
    """設定済みのOnline API接続先へGETし、レスポンスから項目候補(パス+サンプル値)を抽出する。

    将来バックエンドAPIのレスポンスは{"metadata": ..., "response": [...]}という
    envelope形式を想定しているため、"response"フィールドがあればその中身を、
    無ければレスポンス全体を対象にフラット化する(metadataは見ない)。
    """
    if not config.base_url:
        return DiscoverFieldsResult(ok=False, message=translate("api_test.base_url_missing", lang))

    headers = build_auth_headers(config)
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(config.base_url, headers=headers)
    except httpx.TimeoutException:
        return DiscoverFieldsResult(ok=False, message=translate("api_test.timeout", lang))
    except httpx.RequestError as exc:
        return DiscoverFieldsResult(ok=False, message=translate("api_test.connection_failed", lang, error=exc))

    try:
        body = response.json()
    except ValueError:
        return DiscoverFieldsResult(ok=False, message=translate("api_discovery.invalid_json", lang))

    data = body.get("response", body) if isinstance(body, dict) else body
    all_fields = _flatten(data)
    if not all_fields:
        return DiscoverFieldsResult(ok=False, message=translate("api_discovery.no_fields", lang))

    return DiscoverFieldsResult(
        ok=True,
        fields=all_fields[:MAX_FIELDS],
        truncated=len(all_fields) > MAX_FIELDS,
    )


def _flatten(value: object, prefix: str = "") -> list[DiscoveredField]:
    if isinstance(value, dict):
        results = []
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            results.extend(_flatten(child, child_prefix))
        return results
    if isinstance(value, list):
        results = []
        for index, child in enumerate(value):
            child_prefix = f"{prefix}.{index}" if prefix else str(index)
            results.extend(_flatten(child, child_prefix))
        return results
    if not prefix:
        return []
    return [DiscoveredField(path=prefix, value=_stringify(value))]


def _stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)
