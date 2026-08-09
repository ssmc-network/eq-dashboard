from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from repositories.api_config_repository import ApiConfigRepository
from schemas.layout import LayoutDefinition
from services.api_discovery_service import DiscoveredField, DiscoverFieldsResult
from services.layout_service import save_layout
from tests.conftest import IsolatedPaths


def test_dashboard_renders_known_layout(client: TestClient, sample_layout: dict) -> None:
    response = client.get("/ui/dashboard/line-a")

    assert response.status_code == 200
    assert "Line A" in response.text


def test_dashboard_404_for_unknown_layout(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = client.get("/ui/dashboard/does-not-exist")

    assert response.status_code == 404


def test_dashboard_falls_back_to_another_canvas_when_requested_one_is_missing(
    client: TestClient, sample_layout: dict
) -> None:
    save_layout(
        LayoutDefinition.model_validate(
            {
                "schemaVersion": "1.0",
                "layout": {"id": "room-b", "name": "Room B", "width": 400, "height": 300},
                "items": [],
            }
        )
    )

    response = client.get("/ui/dashboard/does-not-exist")

    assert response.status_code == 200
    assert "does-not-exist" in response.text
    assert "Line A" in response.text or "Room B" in response.text


def test_dashboard_shows_no_fallback_notice_for_existing_layout(client: TestClient, sample_layout: dict) -> None:
    response = client.get("/ui/dashboard/line-a")

    assert response.status_code == 200
    assert "dashboard-fallback-notice" not in response.text


def test_dashboard_has_fullscreen_button(client: TestClient, sample_layout: dict) -> None:
    response = client.get("/ui/dashboard/line-a")

    assert 'id="fullscreen-btn"' in response.text
    assert 'id="fullscreen-exit-btn"' not in response.text


def test_layout_editor_has_no_fullscreen_button(client: TestClient, sample_layout: dict) -> None:
    """全画面表示はダッシュボード専用の機能で、レイアウト編集画面には不要なため。"""
    response = client.get("/ui/layouts/line-a/edit")

    assert 'id="fullscreen-btn"' not in response.text


def test_layouts_list_shows_known_layout(client: TestClient, sample_layout: dict) -> None:
    response = client.get("/ui/layouts")

    assert response.status_code == 200
    assert "Line A" in response.text


def test_layout_editor_new_renders_blank_form(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    """新規キャンバス用の空プレースホルダーがLayoutMetaのmin_length制約に引っかからないことの確認。"""
    response = client.get("/ui/layouts/new")

    assert response.status_code == 200
    assert 'id="meta-id" value=""' in response.text


def test_layout_editor_new_uses_widescreen_default_size(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = client.get("/ui/layouts/new")

    assert '"width": 1920' in response.text
    assert '"height": 1080' in response.text


def test_layout_editor_has_no_width_height_inputs(client: TestClient, sample_layout: dict) -> None:
    """キャンバスサイズは固定値運用のため、編集画面のUIからは変更できない(内部的には可変のまま)。"""
    response = client.get("/ui/layouts/line-a/edit")

    assert 'id="meta-width"' not in response.text
    assert 'id="meta-height"' not in response.text


def test_layout_editor_has_zoom_controls_and_minimap(client: TestClient, sample_layout: dict) -> None:
    """キャンバスサイズが固定値のため、拡大縮小とミニマップで編集しやすくする。"""
    response = client.get("/ui/layouts/line-a/edit")

    assert 'id="zoom-out-btn"' in response.text
    assert 'id="zoom-in-btn"' in response.text
    assert 'id="zoom-reset-btn"' in response.text
    assert 'id="editor-minimap"' in response.text


def test_tag_mapping_create_then_appears_in_table(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = client.post(
        "/ui/tag-mappings",
        data={"tag_id": "tag-a", "api_field": "line_a.pump.run_state", "running_value": "1"},
    )

    assert response.status_code == 200
    assert "tag-a" in response.text
    assert "line_a.pump.run_state" in response.text


def test_tag_mapping_table_shows_usage_for_used_and_unused_tags(client: TestClient, sample_layout: dict) -> None:
    client.post("/ui/tag-mappings", data={"tag_id": "tag-a", "api_field": "field-a"})
    response = client.post("/ui/tag-mappings", data={"tag_id": "tag-unused", "api_field": "field-b"})

    assert "Line A / Pump" in response.text
    assert "未使用" in response.text


def test_tag_mapping_create_duplicate_shows_error(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    client.post("/ui/tag-mappings", data={"tag_id": "tag-a", "api_field": "field-1"})

    response = client.post("/ui/tag-mappings", data={"tag_id": "tag-a", "api_field": "field-2"})

    assert response.status_code == 200
    assert "既に登録されています" in response.text


def test_tag_mappings_discover_shows_fetched_fields(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    field = DiscoveredField(path="line_a.transport_a.run_state", value="1")
    fake_result = DiscoverFieldsResult(ok=True, fields=[field])
    with patch("routes.ui.discover_fields", AsyncMock(return_value=fake_result)):
        response = client.post("/ui/tag-mappings/discover")

    assert response.status_code == 200
    assert "line_a.transport_a.run_state" in response.text


def test_tag_mappings_discover_shows_error_message(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    fake_result = DiscoverFieldsResult(ok=False, message="接続先URLが設定されていません。")
    with patch("routes.ui.discover_fields", AsyncMock(return_value=fake_result)):
        response = client.post("/ui/tag-mappings/discover")

    assert response.status_code == 200
    assert "接続先URLが設定されていません。" in response.text


def test_tag_mappings_bulk_create_creates_selected_mappings(
    client: TestClient, isolated_provider: IsolatedPaths
) -> None:
    response = client.post(
        "/ui/tag-mappings/bulk-create",
        data={"selected_paths": ["line_a.transport_a.run_state", "line_a.press_b.run_state"]},
    )

    assert response.status_code == 200
    assert "line_a_transport_a_run_state" in response.text
    assert "line_a_press_b_run_state" in response.text
    assert "line_a.transport_a.run_state" in response.text


def test_tag_mappings_bulk_create_skips_already_registered_tag_id(
    client: TestClient, isolated_provider: IsolatedPaths
) -> None:
    client.post("/ui/tag-mappings", data={"tag_id": "line_a_transport_a_run_state", "api_field": "manual"})

    response = client.post(
        "/ui/tag-mappings/bulk-create",
        data={"selected_paths": ["line_a.transport_a.run_state"]},
    )

    assert response.status_code == 200
    assert "0件作成" in response.text
    assert "1件は既存のためスキップ" in response.text


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


def test_layout_delete_removes_it_from_list(client: TestClient, sample_layout: dict) -> None:
    response = client.request("DELETE", "/ui/layouts/line-a")

    assert response.status_code == 200
    assert "Line A" not in response.text


def test_layout_delete_missing_is_noop(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = client.request("DELETE", "/ui/layouts/does-not-exist")

    assert response.status_code == 200


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
            "language": "en",
            "operation_mode": "offline",
            "default_layout_id": "line-a",
            "default_refresh_interval": "30",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.cookies["theme"] == "dark"
    assert response.cookies["language"] == "en"
    assert response.cookies["default_layout_id"] == "line-a"
    assert response.cookies["default_refresh_interval"] == "30"


def test_settings_save_rejects_invalid_language(client: TestClient, sample_layout: dict) -> None:
    response = client.post(
        "/ui/settings",
        data={
            "theme": "system",
            "language": "fr",
            "operation_mode": "offline",
            "default_layout_id": "line-a",
            "default_refresh_interval": "30",
        },
        follow_redirects=False,
    )

    assert response.cookies["language"] == "ja"


def test_dashboard_renders_in_english_when_language_cookie_set(client: TestClient, sample_layout: dict) -> None:
    client.cookies.set("language", "en")

    response = client.get("/ui/dashboard/line-a")

    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "ダッシュボード" not in response.text
