from providers.json_status_provider import JsonStatusProvider, LayoutFileNotFoundError
from schemas.layout import LayoutDefinition, LayoutMeta

_provider = JsonStatusProvider()


class LayoutNotFoundError(Exception):
    pass


def list_layouts() -> list[LayoutMeta]:
    return _provider.list_layouts()


def get_layout(layout_id: str) -> LayoutDefinition:
    try:
        return _provider.load_layout(layout_id)
    except LayoutFileNotFoundError as exc:
        raise LayoutNotFoundError(layout_id) from exc
