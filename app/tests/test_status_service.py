import pytest

from schemas.status import StatusSnapshot
from services.layout_service import LayoutNotFoundError
from services.status_service import get_dashboard, save_status
from tests.conftest import IsolatedPaths


def test_get_dashboard_joins_layout_items_to_status_by_tag_id(
    isolated_provider: IsolatedPaths, sample_layout: dict
) -> None:
    layout, boxes = get_dashboard("line-a")

    assert layout.layout.id == "line-a"
    by_id = {box.id: box for box in boxes}
    assert by_id["m1"].status_value == "running"
    assert by_id["m1"].status_label == "稼働中"


def test_get_dashboard_marks_unmatched_tag_as_unknown(isolated_provider: IsolatedPaths, sample_layout: dict) -> None:
    _, boxes = get_dashboard("line-a")

    by_id = {box.id: box for box in boxes}
    assert by_id["m2"].status_value == "unknown"


def test_get_dashboard_raises_for_missing_layout(isolated_provider: IsolatedPaths) -> None:
    with pytest.raises(LayoutNotFoundError):
        get_dashboard("does-not-exist")


def test_save_status_persists_and_is_reloadable(isolated_provider: IsolatedPaths, sample_layout: dict) -> None:
    new_status = StatusSnapshot.model_validate(
        {
            "schemaVersion": "1.0",
            "generatedAt": "2026-02-02T00:00:00+09:00",
            "statuses": [
                {
                    "tagId": "tag-a",
                    "value": "alarm",
                    "severity": "critical",
                    "updatedAt": "2026-02-02T00:00:00+09:00",
                }
            ],
        }
    )
    save_status(new_status)

    _, boxes = get_dashboard("line-a")
    by_id = {box.id: box for box in boxes}
    assert by_id["m1"].status_value == "alarm"
