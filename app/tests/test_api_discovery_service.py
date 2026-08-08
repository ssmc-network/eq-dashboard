import asyncio
import json
from collections.abc import Iterator
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from schemas.api_config import ApiConfig
from services.api_discovery_service import MAX_FIELDS, discover_fields


def _mock_response(status_code: int, body: object) -> httpx.Response:
    return httpx.Response(
        status_code,
        content=json.dumps(body).encode("utf-8"),
        request=httpx.Request("GET", "http://example.com"),
    )


@pytest.fixture
def mock_async_client() -> Iterator[AsyncMock]:
    with patch("services.api_discovery_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        yield mock_client


def test_discover_fields_missing_base_url(mock_async_client: AsyncMock) -> None:
    result = asyncio.run(discover_fields(ApiConfig(baseUrl="")))

    assert not result.ok
    mock_async_client.get.assert_not_called()


def test_discover_fields_flattens_envelope_response(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.return_value = _mock_response(
        200,
        {
            "metadata": {"should": "be-ignored"},
            "response": {"line_a": {"transport_a": {"run_state": "1"}}},
        },
    )

    result = asyncio.run(discover_fields(ApiConfig(baseUrl="http://example.com")))

    assert result.ok
    assert [(f.path, f.value) for f in result.fields] == [("line_a.transport_a.run_state", "1")]


def test_discover_fields_flattens_list_with_index_prefix(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.return_value = _mock_response(
        200,
        {"response": [{"run_state": "1"}, {"run_state": "0"}]},
    )

    result = asyncio.run(discover_fields(ApiConfig(baseUrl="http://example.com")))

    paths = [f.path for f in result.fields]
    assert paths == ["0.run_state", "1.run_state"]


def test_discover_fields_falls_back_to_whole_body_without_response_key(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.return_value = _mock_response(200, {"run_state": "1"})

    result = asyncio.run(discover_fields(ApiConfig(baseUrl="http://example.com")))

    assert result.ok
    assert [(f.path, f.value) for f in result.fields] == [("run_state", "1")]


def test_discover_fields_reports_no_fields_for_empty_response(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.return_value = _mock_response(200, {"response": {}})

    result = asyncio.run(discover_fields(ApiConfig(baseUrl="http://example.com")))

    assert not result.ok


def test_discover_fields_reports_invalid_json(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.return_value = httpx.Response(
        200, content=b"not json", request=httpx.Request("GET", "http://example.com")
    )

    result = asyncio.run(discover_fields(ApiConfig(baseUrl="http://example.com")))

    assert not result.ok


def test_discover_fields_truncates_when_too_many(mock_async_client: AsyncMock) -> None:
    body = {"response": {f"field_{i}": str(i) for i in range(MAX_FIELDS + 10)}}
    mock_async_client.get.return_value = _mock_response(200, body)

    result = asyncio.run(discover_fields(ApiConfig(baseUrl="http://example.com")))

    assert result.ok
    assert result.truncated
    assert len(result.fields) == MAX_FIELDS


def test_discover_fields_timeout(mock_async_client: AsyncMock) -> None:
    mock_async_client.get.side_effect = httpx.TimeoutException("timed out")

    result = asyncio.run(discover_fields(ApiConfig(baseUrl="http://example.com")))

    assert not result.ok
