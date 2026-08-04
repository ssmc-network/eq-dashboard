from core.log_modules import log_application
from providers.json_status_provider import JsonStatusProvider, LayoutFileNotFoundError
from schemas.layout import LayoutDefinition, LayoutMeta

_provider = JsonStatusProvider()
logger = log_application(__name__)


class LayoutNotFoundError(Exception):
    pass


def list_layouts() -> list[LayoutMeta]:
    return _provider.list_layouts()


def get_layout(layout_id: str) -> LayoutDefinition:
    try:
        return _provider.load_layout(layout_id)
    except LayoutFileNotFoundError as exc:
        raise LayoutNotFoundError(layout_id) from exc


def layout_exists(layout_id: str) -> bool:
    return any(meta.id == layout_id for meta in list_layouts())


def save_layout(layout: LayoutDefinition) -> None:
    _provider.save_layout(layout)
    logger.info(
        "layout saved",
        extra={"argument": {"layout_id": layout.layout.id, "item_count": len(layout.items)}},
    )
