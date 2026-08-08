from dataclasses import dataclass
from datetime import datetime

from core.i18n import DEFAULT_LANGUAGE, translate
from core.log_modules import log_application
from providers.json_status_provider import JsonStatusProvider
from schemas.layout import LayoutDefinition
from schemas.status import StatusSnapshot
from services.layout_service import get_layout

STATUS_KEYS = {
    "running": "status.running",
    "stopped": "status.stopped",
    "alarm": "status.alarm",
    "unknown": "status.unknown",
}

_provider = JsonStatusProvider()
logger = log_application(__name__)


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


def get_dashboard(layout_id: str, lang: str = DEFAULT_LANGUAGE) -> tuple[LayoutDefinition, list[DashboardBox]]:
    layout = get_layout(layout_id)
    status = _provider.load_status()
    status_by_tag = {s.tag_id: s for s in status.statuses}

    boxes = []
    for item in layout.items:
        matched = status_by_tag.get(item.tag_id)
        value = matched.value if matched else "unknown"
        updated_at = matched.updated_at if matched else status.generated_at
        key = STATUS_KEYS.get(value)
        boxes.append(
            DashboardBox(
                id=item.id,
                label=item.label,
                x=item.x,
                y=item.y,
                w=item.w,
                h=item.h,
                status_value=value,
                status_label=translate(key, lang) if key else value,
                updated_at=updated_at,
            )
        )
    return layout, boxes


def save_status(status: StatusSnapshot) -> None:
    _provider.save_status(status)
    logger.info("status saved", extra={"argument": {"status_count": len(status.statuses)}})
