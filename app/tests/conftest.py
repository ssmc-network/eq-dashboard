import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import routes.api as api_routes
import routes.ui as ui_routes
from providers.json_status_provider import JsonStatusProvider
from repositories.api_config_repository import ApiConfigRepository
from services import layout_service, status_service, tag_mapping_service


@dataclass
class IsolatedPaths:
    provider: JsonStatusProvider
    layouts_dir: Path
    status_path: Path
    tag_mappings_path: Path


@pytest.fixture
def isolated_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> IsolatedPaths:
    """レイアウト/ステータス/タグマッピングの各サービスが使うproviderを一時ディレクトリに差し替える。

    data/sample/*.json には絶対に触れない。
    """
    layouts_dir = tmp_path / "layouts"
    layouts_dir.mkdir()
    status_path = tmp_path / "status.json"
    tag_mappings_path = tmp_path / "tag_mappings.json"

    status_path.write_text(
        json.dumps(
            {
                "schemaVersion": "1.0",
                "generatedAt": "2026-01-01T00:00:00+09:00",
                "statuses": [
                    {
                        "tagId": "tag-a",
                        "value": "running",
                        "severity": "normal",
                        "updatedAt": "2026-01-01T00:00:00+09:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    tag_mappings_path.write_text(json.dumps({"schemaVersion": "1.0", "mappings": []}), encoding="utf-8")

    provider = JsonStatusProvider(
        layouts_dir=layouts_dir,
        status_path=status_path,
        tag_mappings_path=tag_mappings_path,
    )

    monkeypatch.setattr(layout_service, "_provider", provider)
    monkeypatch.setattr(status_service, "_provider", provider)
    monkeypatch.setattr(tag_mapping_service, "_provider", provider)
    monkeypatch.setattr(api_routes, "_provider", provider)

    return IsolatedPaths(
        provider=provider,
        layouts_dir=layouts_dir,
        status_path=status_path,
        tag_mappings_path=tag_mappings_path,
    )


@pytest.fixture
def isolated_api_config_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ApiConfigRepository:
    """Online設定のAPI接続設定を一時ファイルに差し替える。"""
    config_path = tmp_path / "api_config.json"
    config_path.write_text(
        json.dumps({"baseUrl": "", "authType": "none", "apiKeyHeader": "X-API-Key", "credential": ""}),
        encoding="utf-8",
    )
    repo = ApiConfigRepository(path=config_path)
    monkeypatch.setattr(ui_routes, "_api_config_repo", repo)
    return repo


@pytest.fixture
def sample_layout(isolated_provider: IsolatedPaths) -> dict:
    """line-a という id のキャンバスを1件用意する。tag-a はstatus.jsonにある、tag-unknown は無い。"""
    layout_dir = isolated_provider.layouts_dir / "line-a"
    layout_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schemaVersion": "1.0",
        "layout": {"id": "line-a", "name": "Line A", "width": 900, "height": 420},
        "items": [
            {"id": "m1", "label": "Pump", "x": 0, "y": 0, "w": 10, "h": 10, "tagId": "tag-a"},
            {"id": "m2", "label": "Valve", "x": 0, "y": 0, "w": 10, "h": 10, "tagId": "tag-unknown"},
        ],
    }
    (layout_dir / "layout.json").write_text(json.dumps(payload), encoding="utf-8")
    return payload


@pytest.fixture
def client(isolated_provider: IsolatedPaths, isolated_api_config_repo: ApiConfigRepository) -> TestClient:
    from main import app

    return TestClient(app)
