import asyncio
from collections.abc import Iterator
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from schemas.api_config import ApiConfig
from services.api_test_service import test_connection as run_connection_test


def _mock_response(status_code: int) -> httpx.Response:
    return httpx.Response(status_code, request=httpx.Request("GET", "http://example.com"))


@pytest.fixture
def mock_async_client() -> Iterator[AsyncMock]:
    with patch("services.api_test_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        yield mock_client


def test_connection_missing_base_url_fails_without_request(mock_async_client: AsyncMock) -> None:
    result = asyncio.run(run_connection_test(ApiConfig(baseUrl="")))

    assert not result.ok
    mock_async_client.get.assert_not_called()


def test_connection_success(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.return_value = _mock_response(200)

    result = asyncio.run(run_connection_test(ApiConfig(baseUrl="http://example.com")))

    assert result.ok
    assert result.status_code == 200


def test_connection_auth_failure(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.return_value = _mock_response(401)

    result = asyncio.run(run_connection_test(ApiConfig(baseUrl="http://example.com")))

    assert not result.ok
    assert result.status_code == 401
    assert "認証" in result.message


def test_connection_error_response(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.return_value = _mock_response(500)

    result = asyncio.run(run_connection_test(ApiConfig(baseUrl="http://example.com")))

    assert not result.ok
    assert result.status_code == 500


def test_connection_timeout(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.side_effect = httpx.TimeoutException("timed out")

    result = asyncio.run(run_connection_test(ApiConfig(baseUrl="http://example.com")))

    assert not result.ok
    assert "タイムアウト" in result.message


def test_connection_request_error(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.side_effect = httpx.ConnectError("boom")

    result = asyncio.run(run_connection_test(ApiConfig(baseUrl="http://example.com")))

    assert not result.ok


def test_connection_sends_bearer_auth_header(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.return_value = _mock_response(200)

    asyncio.run(
        run_connection_test(ApiConfig(baseUrl="http://example.com", authType="bearer", credential="secret-token"))
    )

    _, kwargs = mock_async_client.get.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer secret-token"


def test_connection_sends_api_key_header(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.return_value = _mock_response(200)

    asyncio.run(
        run_connection_test(
            ApiConfig(
                baseUrl="http://example.com",
                authType="api_key",
                apiKeyHeader="X-Custom-Key",
                credential="secret-key",
            )
        )
    )

    _, kwargs = mock_async_client.get.call_args
    assert kwargs["headers"]["X-Custom-Key"] == "secret-key"
