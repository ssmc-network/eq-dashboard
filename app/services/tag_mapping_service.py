from core.log_modules import log_application
from providers.json_status_provider import JsonStatusProvider
from schemas.tag_mapping import TagMapping, TagMappingSet
from services.layout_service import get_layout, list_layouts

_provider = JsonStatusProvider()
logger = log_application(__name__)

SCHEMA_VERSION = "1.0"


class TagMappingExistsError(Exception):
    pass


class TagMappingNotFoundError(Exception):
    pass


def list_tag_mappings() -> list[TagMapping]:
    return _provider.load_tag_mappings().mappings


def get_tag_mapping(tag_id: str) -> TagMapping | None:
    return next((m for m in list_tag_mappings() if m.tag_id == tag_id), None)


def get_tag_usage() -> dict[str, list[str]]:
    """tagId -> このtagIdを使っている「キャンバス名 / 装置ラベル」のリスト。"""
    usage: dict[str, list[str]] = {}
    for meta in list_layouts():
        layout = get_layout(meta.id)
        for item in layout.items:
            if not item.tag_id:
                continue
            usage.setdefault(item.tag_id, []).append(f"{layout.layout.name} / {item.label}")
    return usage


def create_tag_mapping(mapping: TagMapping) -> None:
    mappings = list_tag_mappings()
    if any(m.tag_id == mapping.tag_id for m in mappings):
        raise TagMappingExistsError(mapping.tag_id)
    mappings.append(mapping)
    _save(mappings)
    logger.info("tag mapping created", extra={"argument": {"tag_id": mapping.tag_id}})


def update_tag_mapping(tag_id: str, mapping: TagMapping) -> None:
    mappings = list_tag_mappings()
    index = next((i for i, m in enumerate(mappings) if m.tag_id == tag_id), None)
    if index is None:
        raise TagMappingNotFoundError(tag_id)
    mappings[index] = mapping
    _save(mappings)
    logger.info("tag mapping updated", extra={"argument": {"tag_id": tag_id}})


def delete_tag_mapping(tag_id: str) -> None:
    mappings = [m for m in list_tag_mappings() if m.tag_id != tag_id]
    _save(mappings)
    logger.info("tag mapping deleted", extra={"argument": {"tag_id": tag_id}})


def _save(mappings: list[TagMapping]) -> None:
    _provider.save_tag_mappings(TagMappingSet(schemaVersion=SCHEMA_VERSION, mappings=mappings))
