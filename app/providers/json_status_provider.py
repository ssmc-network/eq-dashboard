import json
from pathlib import Path

from schemas.layout import LayoutDefinition, LayoutMeta
from schemas.status import StatusSnapshot

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"
LAYOUTS_DIR = SAMPLE_DIR / "layouts"
STATUS_PATH = SAMPLE_DIR / "status.json"


class LayoutFileNotFoundError(Exception):
    pass


class JsonStatusProvider:
    def __init__(self, layouts_dir: Path = LAYOUTS_DIR, status_path: Path = STATUS_PATH) -> None:
        self._layouts_dir = layouts_dir
        self._status_path = status_path

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

    def save_layout(self, layout: LayoutDefinition) -> None:
        layout_dir = self._layouts_dir / layout.layout.id
        layout_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(layout.model_dump(by_alias=True), ensure_ascii=False, indent=2)
        (layout_dir / "layout.json").write_text(payload, encoding="utf-8")

    def load_status(self) -> StatusSnapshot:
        data = json.loads(self._status_path.read_text(encoding="utf-8"))
        return StatusSnapshot.model_validate(data)

    def save_status(self, status: StatusSnapshot) -> None:
        payload = json.dumps(status.model_dump(by_alias=True, mode="json"), ensure_ascii=False, indent=2)
        self._status_path.write_text(payload, encoding="utf-8")

    def _layout_path(self, layout_id: str) -> Path:
        path = self._layouts_dir / layout_id / "layout.json"
        if not path.exists():
            raise LayoutFileNotFoundError(layout_id)
        return path
