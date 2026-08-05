import pytest
from pydantic import ValidationError

from schemas.api_config import ApiConfig
from schemas.layout import LayoutDefinition
from schemas.status import StatusSnapshot
from schemas.tag_mapping import TagMapping, TagMappingSet


def test_layout_definition_round_trips_camel_case_alias() -> None:
    raw = {
        "schemaVersion": "1.0",
        "layout": {"id": "line-a", "name": "Line A", "width": 900, "height": 420},
        "items": [{"id": "m1", "label": "Pump", "x": 1, "y": 2, "w": 3, "h": 4, "tagId": "tag-a"}],
    }
    layout = LayoutDefinition.model_validate(raw)

    assert layout.schema_version == "1.0"
    assert layout.items[0].tag_id == "tag-a"
    assert layout.model_dump(by_alias=True) == raw


def test_status_snapshot_round_trips_camel_case_alias() -> None:
    raw = {
        "schemaVersion": "1.0",
        "generatedAt": "2026-01-01T00:00:00+09:00",
        "statuses": [
            {"tagId": "tag-a", "value": "running", "severity": "normal", "updatedAt": "2026-01-01T00:00:00+09:00"}
        ],
    }
    status = StatusSnapshot.model_validate(raw)

    assert status.statuses[0].tag_id == "tag-a"
    assert status.model_dump(by_alias=True, mode="json") == raw


def test_tag_mapping_set_round_trips_camel_case_alias() -> None:
    raw = {
        "schemaVersion": "1.0",
        "mappings": [
            {
                "tagId": "tag-a",
                "apiField": "line_a.pump.run_state",
                "runningValue": "1",
                "stoppedValue": "0",
                "alarmValue": "9",
            }
        ],
    }
    mapping_set = TagMappingSet.model_validate(raw)

    assert mapping_set.mappings[0].tag_id == "tag-a"
    assert mapping_set.model_dump(by_alias=True) == raw


def test_tag_mapping_defaults_blank_values() -> None:
    mapping = TagMapping(tagId="tag-a", apiField="field")

    assert mapping.running_value == ""
    assert mapping.stopped_value == ""
    assert mapping.alarm_value == ""


def test_api_config_defaults() -> None:
    config = ApiConfig()

    assert config.base_url == ""
    assert config.auth_type == "none"
    assert config.api_key_header == "X-API-Key"
    assert config.credential == ""


@pytest.mark.parametrize("blank", ["", "   "])
def test_tag_mapping_rejects_blank_tag_id(blank: str) -> None:
    with pytest.raises(ValidationError):
        TagMapping(tagId=blank, apiField="field")


@pytest.mark.parametrize("blank", ["", "   "])
def test_tag_mapping_rejects_blank_api_field(blank: str) -> None:
    with pytest.raises(ValidationError):
        TagMapping(tagId="tag-a", apiField=blank)


def test_tag_mapping_strips_surrounding_whitespace() -> None:
    mapping = TagMapping(tagId="  tag-a  ", apiField="  field  ")

    assert mapping.tag_id == "tag-a"
    assert mapping.api_field == "field"


def test_layout_meta_rejects_blank_id_and_name() -> None:
    with pytest.raises(ValidationError):
        LayoutDefinition.model_validate(
            {"schemaVersion": "1.0", "layout": {"id": "", "name": "x", "width": 10, "height": 10}, "items": []}
        )


@pytest.mark.parametrize(("field", "value"), [("width", 0), ("width", -1), ("height", 0), ("height", -1)])
def test_layout_meta_rejects_non_positive_dimensions(field: str, value: int) -> None:
    layout_meta = {"id": "x", "name": "x", "width": 10, "height": 10, field: value}
    with pytest.raises(ValidationError):
        LayoutDefinition.model_validate({"schemaVersion": "1.0", "layout": layout_meta, "items": []})


@pytest.mark.parametrize(("field", "value"), [("w", 0), ("w", -1), ("h", 0), ("h", -1), ("x", -1), ("y", -1)])
def test_layout_item_rejects_invalid_geometry(field: str, value: int) -> None:
    item = {"id": "m1", "label": "Pump", "x": 0, "y": 0, "w": 10, "h": 10, "tagId": "tag-a", field: value}
    with pytest.raises(ValidationError):
        LayoutDefinition.model_validate(
            {
                "schemaVersion": "1.0",
                "layout": {"id": "line-a", "name": "Line A", "width": 900, "height": 420},
                "items": [item],
            }
        )


def test_layout_item_allows_blank_tag_id() -> None:
    """タグ未設定のまま装置を追加できる、既存のレイアウト編集フローを壊さないための確認。"""
    layout = LayoutDefinition.model_validate(
        {
            "schemaVersion": "1.0",
            "layout": {"id": "line-a", "name": "Line A", "width": 900, "height": 420},
            "items": [{"id": "m1", "label": "Pump", "x": 0, "y": 0, "w": 10, "h": 10, "tagId": ""}],
        }
    )

    assert layout.items[0].tag_id == ""
