import time
from dataclasses import dataclass

import httpx

from core.i18n import DEFAULT_LANGUAGE, translate
from core.log_modules import log_application
from schemas.api_config import ApiConfig

TIMEOUT_SECONDS = 5.0
HTTP_ERROR_THRESHOLD = 400

logger = log_application(__name__)


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


async def test_connection(config: ApiConfig, lang: str = DEFAULT_LANGUAGE) -> ApiTestResult:
    if not config.base_url:
        result = ApiTestResult(ok=False, message=translate("api_test.base_url_missing", lang))
        _log_result(config, result)
        return result

    headers = _build_headers(config)
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(config.base_url, headers=headers)
    except httpx.TimeoutException:
        result = ApiTestResult(ok=False, message=translate("api_test.timeout", lang))
        _log_result(config, result)
        return result
    except httpx.RequestError as exc:
        result = ApiTestResult(ok=False, message=translate("api_test.connection_failed", lang, error=exc))
        _log_result(config, result)
        return result

    elapsed_ms = int((time.monotonic() - start) * 1000)

    if response.status_code in (401, 403):
        result = ApiTestResult(
            ok=False,
            message=translate("api_test.auth_failed", lang, status=response.status_code),
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
        )
    elif response.status_code >= HTTP_ERROR_THRESHOLD:
        result = ApiTestResult(
            ok=False,
            message=translate("api_test.error_response", lang, status=response.status_code),
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
        )
    else:
        result = ApiTestResult(
            ok=True,
            message=translate("api_test.success", lang, status=response.status_code, elapsed=elapsed_ms),
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
        )
    _log_result(config, result)
    return result


def _log_result(config: ApiConfig, result: ApiTestResult) -> None:
    logger.info(
        "api connectivity test",
        extra={
            "argument": {
                "base_url": config.base_url,
                "auth_type": config.auth_type,
                "ok": result.ok,
                "status_code": result.status_code,
                "elapsed_ms": result.elapsed_ms,
            }
        },
    )
