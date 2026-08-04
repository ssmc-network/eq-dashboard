import time
from dataclasses import dataclass

import httpx

from schemas.api_config import ApiConfig

TIMEOUT_SECONDS = 5.0
HTTP_ERROR_THRESHOLD = 400


@dataclass
class ApiTestResult:
    ok: bool
    message: str
    status_code: int | None = None
    elapsed_ms: int | None = None


def _build_headers(config: ApiConfig) -> dict[str, str]:
    if config.auth_type == "api_key" and config.credential:
        return {config.api_key_header or "X-API-Key": config.credential}
    if config.auth_type == "bearer" and config.credential:
        return {"Authorization": f"Bearer {config.credential}"}
    return {}


async def test_connection(config: ApiConfig) -> ApiTestResult:
    if not config.base_url:
        return ApiTestResult(ok=False, message="接続先URLが設定されていません。")

    headers = _build_headers(config)
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(config.base_url, headers=headers)
    except httpx.TimeoutException:
        return ApiTestResult(ok=False, message="接続がタイムアウトしました。")
    except httpx.RequestError as exc:
        return ApiTestResult(ok=False, message=f"接続に失敗しました: {exc}")

    elapsed_ms = int((time.monotonic() - start) * 1000)

    if response.status_code in (401, 403):
        return ApiTestResult(
            ok=False,
            message=f"認証に失敗しました(HTTP {response.status_code})。",
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
        )
    if response.status_code >= HTTP_ERROR_THRESHOLD:
        return ApiTestResult(
            ok=False,
            message=f"接続はできましたが、エラー応答でした(HTTP {response.status_code})。",
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
        )
    return ApiTestResult(
        ok=True,
        message=f"接続に成功しました(HTTP {response.status_code}, {elapsed_ms}ms)。",
        status_code=response.status_code,
        elapsed_ms=elapsed_ms,
    )
