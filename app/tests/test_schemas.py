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
