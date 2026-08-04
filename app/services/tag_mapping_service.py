from providers.json_status_provider import JsonStatusProvider
from schemas.tag_mapping import TagMapping, TagMappingSet

_provider = JsonStatusProvider()

SCHEMA_VERSION = "1.0"


class TagMappingExistsError(Exception):
    pass


class TagMappingNotFoundError(Exception):
    pass


def list_tag_mappings() -> list[TagMapping]:
    return _provider.load_tag_mappings().mappings


def get_tag_mapping(tag_id: str) -> TagMapping | None:
    return next((m for m in list_tag_mappings() if m.tag_id == tag_id), None)


def create_tag_mapping(mapping: TagMapping) -> None:
    mappings = list_tag_mappings()
    if any(m.tag_id == mapping.tag_id for m in mappings):
        raise TagMappingExistsError(mapping.tag_id)
    mappings.append(mapping)
    _save(mappings)


def update_tag_mapping(tag_id: str, mapping: TagMapping) -> None:
    mappings = list_tag_mappings()
    index = next((i for i, m in enumerate(mappings) if m.tag_id == tag_id), None)
    if index is None:
        raise TagMappingNotFoundError(tag_id)
    mappings[index] = mapping
    _save(mappings)


def delete_tag_mapping(tag_id: str) -> None:
    mappings = [m for m in list_tag_mappings() if m.tag_id != tag_id]
    _save(mappings)


def _save(mappings: list[TagMapping]) -> None:
    _provider.save_tag_mappings(TagMappingSet(schemaVersion=SCHEMA_VERSION, mappings=mappings))
