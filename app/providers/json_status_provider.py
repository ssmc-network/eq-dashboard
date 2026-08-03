import json
from pathlib import Path

from schemas.layout import LayoutDefinition
from schemas.status import StatusSnapshot

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"


class JsonStatusProvider:
    def __init__(
        self,
        layout_path: Path = SAMPLE_DIR / "layout.json",
        status_path: Path = SAMPLE_DIR / "status.json",
    ) -> None:
        self._layout_path = layout_path
        self._status_path = status_path

    def load_layout(self) -> LayoutDefinition:
        data = json.loads(self._layout_path.read_text(encoding="utf-8"))
        return LayoutDefinition.model_validate(data)

    def load_status(self) -> StatusSnapshot:
        data = json.loads(self._status_path.read_text(encoding="utf-8"))
        return StatusSnapshot.model_validate(data)
