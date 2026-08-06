from services.import_export_service import validate_layout_json, validate_status_json

VALID_LAYOUT_JSON = b"""
{
  "schemaVersion": "1.0",
  "layout": {"id": "line-a", "name": "Line A", "width": 900, "height": 420},
  "items": [{"id": "m1", "label": "Pump", "x": 0, "y": 0, "w": 10, "h": 10, "tagId": "tag-a"}]
}
"""

VALID_STATUS_JSON = b"""
{
  "schemaVersion": "1.0",
  "generatedAt": "2026-01-01T00:00:00+09:00",
  "statuses": [
    {"tagId": "tag-a", "value": "running", "severity": "normal", "updatedAt": "2026-01-01T00:00:00+09:00"}
  ]
}
"""


def test_validate_layout_json_accepts_valid_payload() -> None:
    result = validate_layout_json(VALID_LAYOUT_JSON)

    assert result.ok
    assert result.errors == []
    assert result.summary is not None
    assert result.summary["id"] == "line-a"
    assert result.summary["itemCount"] == 1


def test_validate_layout_json_rejects_malformed_json() -> None:
    result = validate_layout_json(b"{not valid json")

    assert not result.ok
    assert result.summary is None
    assert len(result.errors) == 1


def test_validate_layout_json_rejects_missing_required_field() -> None:
    result = validate_layout_json(b'{"layout": {"id": "x", "name": "x", "width": 1, "height": 1}, "items": []}')

    assert not result.ok
    assert any("schemaVersion" in err or "schema_version" in err for err in result.errors)


def test_validate_status_json_accepts_valid_payload() -> None:
    result = validate_status_json(VALID_STATUS_JSON)

    assert result.ok
    assert result.summary is not None
    assert result.summary["statusCount"] == 1


def test_validate_status_json_rejects_malformed_json() -> None:
    result = validate_status_json(b"not json at all")

    assert not result.ok
    assert result.summary is None


def test_validate_status_json_rejects_wrong_shape() -> None:
    result = validate_status_json(b'{"schemaVersion": "1.0", "statuses": "not-a-list"}')

    assert not result.ok
    assert result.errors
