from dataclasses import dataclass
from datetime import datetime

from providers.json_status_provider import JsonStatusProvider
from schemas.layout import LayoutDefinition, LayoutShape

STATUS_LABELS = {
    "running": "稼働中",
    "stopped": "停止中",
    "alarm": "アラーム",
}

_provider = JsonStatusProvider()


@dataclass
class DeviceMarker:
    id: str
    label: str
    x: int
    y: int
    status_value: str
    status_label: str
    updated_at: datetime


@dataclass
class FloorMap:
    layout: LayoutDefinition
    shapes: list[LayoutShape]
    markers: list[DeviceMarker]


class LayoutNotFoundError(Exception):
    pass


def get_floor_map(layout_id: str) -> FloorMap:
    layout = _provider.load_layout()
    if layout.layout.id != layout_id:
        raise LayoutNotFoundError(layout_id)

    status = _provider.load_status()
    status_by_tag = {s.tag_id: s for s in status.statuses}

    markers = []
    for device in layout.devices:
        matched = status_by_tag.get(device.tag_id)
        value = matched.value if matched else "unknown"
        updated_at = matched.updated_at if matched else status.generated_at
        markers.append(
            DeviceMarker(
                id=device.id,
                label=device.label,
                x=device.x,
                y=device.y,
                status_value=value,
                status_label=STATUS_LABELS.get(value, value),
                updated_at=updated_at,
            )
        )

    return FloorMap(layout=layout, shapes=layout.shapes, markers=markers)
