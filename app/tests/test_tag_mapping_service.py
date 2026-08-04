import pytest

from schemas.tag_mapping import TagMapping
from services.tag_mapping_service import (
    TagMappingExistsError,
    TagMappingNotFoundError,
    create_tag_mapping,
    delete_tag_mapping,
    get_tag_mapping,
    list_tag_mappings,
    update_tag_mapping,
)
from tests.conftest import IsolatedPaths


def test_list_tag_mappings_starts_empty(isolated_provider: IsolatedPaths) -> None:
    assert list_tag_mappings() == []


def test_create_tag_mapping_persists(isolated_provider: IsolatedPaths) -> None:
    create_tag_mapping(TagMapping(tagId="tag-a", apiField="line_a.pump.run_state", runningValue="1"))

    mappings = list_tag_mappings()
    assert len(mappings) == 1
    assert mappings[0].tag_id == "tag-a"
    assert mappings[0].api_field == "line_a.pump.run_state"


def test_create_tag_mapping_duplicate_raises(isolated_provider: IsolatedPaths) -> None:
    create_tag_mapping(TagMapping(tagId="tag-a", apiField="field-1"))

    with pytest.raises(TagMappingExistsError):
        create_tag_mapping(TagMapping(tagId="tag-a", apiField="field-2"))


def test_get_tag_mapping_returns_none_when_missing(isolated_provider: IsolatedPaths) -> None:
    assert get_tag_mapping("does-not-exist") is None


def test_update_tag_mapping_replaces_existing(isolated_provider: IsolatedPaths) -> None:
    create_tag_mapping(TagMapping(tagId="tag-a", apiField="old-field"))

    update_tag_mapping("tag-a", TagMapping(tagId="tag-a", apiField="new-field", runningValue="1"))

    mapping = get_tag_mapping("tag-a")
    assert mapping is not None
    assert mapping.api_field == "new-field"
    assert mapping.running_value == "1"


def test_update_tag_mapping_missing_raises(isolated_provider: IsolatedPaths) -> None:
    with pytest.raises(TagMappingNotFoundError):
        update_tag_mapping("does-not-exist", TagMapping(tagId="does-not-exist", apiField="field"))


def test_delete_tag_mapping_removes_it(isolated_provider: IsolatedPaths) -> None:
    create_tag_mapping(TagMapping(tagId="tag-a", apiField="field"))

    delete_tag_mapping("tag-a")

    assert list_tag_mappings() == []


def test_delete_tag_mapping_missing_is_noop(isolated_provider: IsolatedPaths) -> None:
    delete_tag_mapping("does-not-exist")

    assert list_tag_mappings() == []
