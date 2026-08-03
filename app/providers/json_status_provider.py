import json
from pathlib import Path

from schemas.layout import LayoutDefinition, LayoutMeta
from schemas.status import StatusSnapshot

LAYOUTS_DIR = Path(__file__).resolve().parent.parent / "data" / "sample" / "layouts"


class LayoutFileNotFoundError(Exception):
    pass


class JsonStatusProvider:
    def __init__(self, layouts_dir: Path = LAYOUTS_DIR) -> None:
        self._layouts_dir = layouts_dir

    def list_layouts(self) -> list[LayoutMeta]:
        metas = []
        for layout_dir in sorted(self._layouts_dir.iterdir()):
            layout_file = layout_dir / "layout.json"
            if not layout_file.exists():
                continue
            data = json.loads(layout_file.read_text(encoding="utf-8"))
            metas.append(LayoutDefinition.model_validate(data).layout)
        return metas

    def load_layout(self, layout_id: str) -> LayoutDefinition:
        data = json.loads(self._layout_path(layout_id).read_text(encoding="utf-8"))
        return LayoutDefinition.model_validate(data)

    def load_status(self, layout_id: str) -> StatusSnapshot:
        data = json.loads(self._status_path(layout_id).read_text(encoding="utf-8"))
        return StatusSnapshot.model_validate(data)

    def _layout_path(self, layout_id: str) -> Path:
        path = self._layouts_dir / layout_id / "layout.json"
        if not path.exists():
            raise LayoutFileNotFoundError(layout_id)
        return path

    def _status_path(self, layout_id: str) -> Path:
        path = self._layouts_dir / layout_id / "status.json"
        if not path.exists():
            raise LayoutFileNotFoundError(layout_id)
        return path
