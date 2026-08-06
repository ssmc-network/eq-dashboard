from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from tests.conftest import IsolatedPaths


def test_full_page_404_renders_html_error_page(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = client.get("/ui/dashboard/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")
    assert "ページが見つかりませんでした" in response.text
    assert "EQ Dashboard" in response.text


def test_htmx_404_returns_200_with_inline_error(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = client.get("/ui/dashboard/does-not-exist/items", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "inline-error" in response.text
    assert "ページが見つかりませんでした" in response.text


def test_api_404_stays_json(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = client.get("/api/standalone/layout/export", params={"layout_id": "does-not-exist"})

    assert response.status_code == 404
    assert response.json() == {"detail": "layout not found"}


def test_unhandled_exception_renders_html_500(isolated_provider: IsolatedPaths) -> None:
    no_raise_client = TestClient(app, raise_server_exceptions=False)
    with patch("routes.ui.list_layouts", side_effect=RuntimeError("boom")):
        response = no_raise_client.get("/ui/layouts")

    assert response.status_code == 500
    assert "予期しないエラーが発生しました" in response.text


def test_unhandled_exception_on_htmx_request_returns_200_inline_error(isolated_provider: IsolatedPaths) -> None:
    no_raise_client = TestClient(app, raise_server_exceptions=False)
    with patch("routes.ui.list_layouts", side_effect=RuntimeError("boom")):
        response = no_raise_client.get("/ui/layouts", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "inline-error" in response.text


def test_unhandled_exception_on_api_route_stays_json(isolated_provider: IsolatedPaths) -> None:
    no_raise_client = TestClient(app, raise_server_exceptions=False)
    with patch("routes.api.get_layout", side_effect=RuntimeError("boom")):
        response = no_raise_client.get("/api/standalone/layout/export", params={"layout_id": "line-a"})

    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}
