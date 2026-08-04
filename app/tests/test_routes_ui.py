from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from repositories.api_config_repository import ApiConfigRepository
from tests.conftest import IsolatedPaths


def test_dashboard_renders_known_layout(client: TestClient, sample_layout: dict) -> None:
    response = client.get("/ui/dashboard/line-a")

    assert response.status_code == 200
    assert "Line A" in response.text


def test_dashboard_404_for_unknown_layout(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = client.get("/ui/dashboard/does-not-exist")

    assert response.status_code == 404


def test_layouts_list_shows_known_layout(client: TestClient, sample_layout: dict) -> None:
    response = client.get("/ui/layouts")

    assert response.status_code == 200
    assert "Line A" in response.text


def test_tag_mapping_create_then_appears_in_table(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = client.post(
        "/ui/tag-mappings",
        data={"tag_id": "tag-a", "api_field": "line_a.pump.run_state", "running_value": "1"},
    )

    assert response.status_code == 200
    assert "tag-a" in response.text
    assert "line_a.pump.run_state" in response.text


def test_tag_mapping_create_duplicate_shows_error(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    client.post("/ui/tag-mappings", data={"tag_id": "tag-a", "api_field": "field-1"})

    response = client.post("/ui/tag-mappings", data={"tag_id": "tag-a", "api_field": "field-2"})

    assert response.status_code == 200
    assert "既に登録されています" in response.text


def test_tag_mapping_update(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    client.post("/ui/tag-mappings", data={"tag_id": "tag-a", "api_field": "old-field"})

    response = client.post("/ui/tag-mappings/tag-a", data={"api_field": "new-field"})

    assert response.status_code == 200
    assert "new-field" in response.text


def test_tag_mapping_update_missing_is_404(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = client.post("/ui/tag-mappings/does-not-exist", data={"api_field": "field"})

    assert response.status_code == 404


def test_tag_mapping_delete(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    client.post("/ui/tag-mappings", data={"tag_id": "tag-a", "api_field": "field"})

    response = client.request("DELETE", "/ui/tag-mappings/tag-a")

    assert response.status_code == 200
    assert "tag-a" not in response.text


def test_api_sources_save_redirects_and_persists(
    client: TestClient, isolated_api_config_repo: ApiConfigRepository
) -> None:
    response = client.post(
        "/ui/api-sources",
        data={"base_url": "https://plc.example.internal", "auth_type": "bearer", "credential": "secret"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    saved = isolated_api_config_repo.load()
    assert saved.base_url == "https://plc.example.internal"
    assert saved.auth_type == "bearer"


def test_api_sources_test_endpoint_reports_success(
    client: TestClient, isolated_api_config_repo: ApiConfigRepository
) -> None:
    with patch("services.api_test_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = httpx.Response(200, request=httpx.Request("GET", "http://example.com"))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        response = client.post("/ui/api-sources/test", data={"base_url": "http://example.com"})

    assert response.status_code == 200
    assert "接続に成功しました" in response.text


def test_settings_save_sets_cookies(client: TestClient, sample_layout: dict) -> None:
    response = client.post(
        "/ui/settings",
        data={
            "theme": "dark",
            "operation_mode": "offline",
            "default_layout_id": "line-a",
            "default_refresh_interval": "30",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.cookies["theme"] == "dark"
    assert response.cookies["default_layout_id"] == "line-a"
    assert response.cookies["default_refresh_interval"] == "30"
