import io
import json
import zipfile

import httpx
from fastapi.testclient import TestClient

from tests.conftest import IsolatedPaths


def _layout_payload(
    layout_id: str = "line-a", name: str = "Line A", width: int = 900, height: int = 420
) -> dict[str, object]:
    return {
        "schemaVersion": "1.0",
        "layout": {"id": layout_id, "name": name, "width": width, "height": height},
        "items": [],
    }


def _post_save(client: TestClient, payload: dict[str, object], **params: str) -> httpx.Response:
    return client.post("/api/layouts/save", params=params, content=json.dumps(payload))


def test_save_new_layout_succeeds(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = _post_save(client, _layout_payload(), original_id="")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "id": "line-a", "name": "Line A"}


def test_save_rejects_invalid_dimensions(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = _post_save(client, _layout_payload(width=0), original_id="")

    assert response.status_code == 422
    assert response.json()["ok"] is False


def test_save_editing_same_layout_does_not_require_confirmation(
    client: TestClient, isolated_provider: IsolatedPaths
) -> None:
    _post_save(client, _layout_payload(), original_id="")

    response = _post_save(client, _layout_payload(name="Line A Updated"), original_id="line-a")

    assert response.status_code == 200
    assert response.json()["name"] == "Line A Updated"


def test_save_new_id_that_collides_needs_confirmation(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    _post_save(client, _layout_payload(), original_id="")

    response = _post_save(client, _layout_payload(), original_id="")

    assert response.status_code == 409
    body = response.json()
    assert body["needsConfirmation"] is True
    assert body["existingName"] == "Line A"


def test_save_new_id_collision_overwrite_true_proceeds(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    _post_save(client, _layout_payload(), original_id="")

    response = _post_save(client, _layout_payload(name="Overwritten"), original_id="", overwrite="true")

    assert response.status_code == 200
    assert response.json()["name"] == "Overwritten"


def test_save_rename_deletes_old_id(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    _post_save(client, _layout_payload(), original_id="")

    response = _post_save(client, _layout_payload(layout_id="line-a-2"), original_id="line-a")

    assert response.status_code == 200
    assert not (isolated_provider.layouts_dir / "line-a").exists()
    assert (isolated_provider.layouts_dir / "line-a-2").exists()


def test_save_rename_onto_existing_id_needs_confirmation(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    _post_save(client, _layout_payload(), original_id="")
    _post_save(client, _layout_payload(layout_id="room-b", name="Room B"), original_id="")

    response = _post_save(client, _layout_payload(layout_id="room-b"), original_id="line-a")

    assert response.status_code == 409
    assert response.json()["existingName"] == "Room B"


def test_export_all_layouts_returns_zip_with_one_entry_per_canvas(
    client: TestClient, isolated_provider: IsolatedPaths
) -> None:
    _post_save(client, _layout_payload(), original_id="")
    _post_save(client, _layout_payload(layout_id="room-b", name="Room B"), original_id="")

    response = client.get("/api/standalone/layout/export/all")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        assert sorted(zf.namelist()) == ["line-a.json", "room-b.json"]
        contents = json.loads(zf.read("line-a.json"))
        assert contents["layout"]["id"] == "line-a"


def test_export_all_layouts_empty_when_no_canvases(client: TestClient, isolated_provider: IsolatedPaths) -> None:
    response = client.get("/api/standalone/layout/export/all")

    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        assert zf.namelist() == []
