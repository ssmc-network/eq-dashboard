import pytest

from schemas.layout import LayoutDefinition
from services.layout_service import (
    LayoutNotFoundError,
    delete_layout,
    get_layout,
    layout_exists,
    list_layouts,
    rename_layout,
    save_layout,
)
from tests.conftest import IsolatedPaths


def _layout(layout_id: str, name: str = "Line A") -> LayoutDefinition:
    return LayoutDefinition.model_validate(
        {
            "schemaVersion": "1.0",
            "layout": {"id": layout_id, "name": name, "width": 900, "height": 420},
            "items": [],
        }
    )


def test_delete_layout_removes_it(isolated_provider: IsolatedPaths) -> None:
    save_layout(_layout("line-a"))
    assert layout_exists("line-a")

    delete_layout("line-a")

    assert not layout_exists("line-a")


def test_delete_layout_missing_is_noop(isolated_provider: IsolatedPaths) -> None:
    delete_layout("does-not-exist")

    assert list_layouts() == []


def test_rename_layout_removes_old_id_and_keeps_new(isolated_provider: IsolatedPaths) -> None:
    save_layout(_layout("line-a"))

    rename_layout("line-a", _layout("line-a-renamed"))

    assert not layout_exists("line-a")
    assert layout_exists("line-a-renamed")


def test_rename_layout_to_same_id_is_a_plain_save(isolated_provider: IsolatedPaths) -> None:
    save_layout(_layout("line-a", name="Old Name"))

    rename_layout("line-a", _layout("line-a", name="New Name"))

    ids = [meta.id for meta in list_layouts()]
    assert ids == ["line-a"]


def test_rename_layout_onto_existing_id_replaces_target_and_drops_source(
    isolated_provider: IsolatedPaths,
) -> None:
    save_layout(_layout("line-a", name="Line A"))
    save_layout(_layout("room-b", name="Room B"))

    rename_layout("line-a", _layout("room-b", name="Merged"))

    assert not layout_exists("line-a")
    ids = [meta.id for meta in list_layouts()]
    assert ids == ["room-b"]


def test_get_layout_raises_for_missing_id(isolated_provider: IsolatedPaths) -> None:
    with pytest.raises(LayoutNotFoundError):
        get_layout("does-not-exist")
