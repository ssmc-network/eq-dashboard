from dataclasses import dataclass
from datetime import datetime

from providers.json_status_provider import JsonStatusProvider
from schemas.layout import LayoutDefinition
from services.layout_service import get_layout

STATUS_LABELS = {
    "running": "稼働中",
    "stopped": "停止中",
    "alarm": "アラーム",
}

_provider = JsonStatusProvider()


@dataclass
class DashboardBox:
    id: str
    label: str
    x: int
    y: int
    w: int
    h: int
    status_value: str
    status_label: str
    updated_at: datetime


def get_dashboard(layout_id: str) -> tuple[LayoutDefinition, list[DashboardBox]]:
    layout = get_layout(layout_id)
    status = _provider.load_status()
    status_by_tag = {s.tag_id: s for s in status.statuses}

    boxes = []
    for item in layout.items:
        matched = status_by_tag.get(item.tag_id)
        value = matched.value if matched else "unknown"
        updated_at = matched.updated_at if matched else status.generated_at
        boxes.append(
            DashboardBox(
                id=item.id,
                label=item.label,
                x=item.x,
                y=item.y,
                w=item.w,
                h=item.h,
                status_value=value,
                status_label=STATUS_LABELS.get(value, value),
                updated_at=updated_at,
            )
        )
    return layout, boxes
