import json
import shutil
from pathlib import Path

from schemas.layout import LayoutDefinition, LayoutMeta
from schemas.status import StatusSnapshot
from schemas.tag_mapping import TagMappingSet

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"
LAYOUTS_DIR = SAMPLE_DIR / "layouts"
STATUS_PATH = SAMPLE_DIR / "status.json"
TAG_MAPPINGS_PATH = SAMPLE_DIR / "tag_mappings.json"


class LayoutFileNotFoundError(Exception):
    pass


class InvalidLayoutIdError(Exception):
    """layout_idがlayouts_dir直下の1階層に収まらない場合に送出する
    (パストラバーサル対策。詳細は_layout_dirを参照)。"""

    pass


class JsonStatusProvider:
    def __init__(
        self,
        layouts_dir: Path = LAYOUTS_DIR,
        status_path: Path = STATUS_PATH,
        tag_mappings_path: Path = TAG_MAPPINGS_PATH,
    ) -> None:
        self._layouts_dir = layouts_dir
        self._status_path = status_path
        self._tag_mappings_path = tag_mappings_path

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
        layout_dir = self._layout_dir(layout.layout.id)
        layout_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(layout.model_dump(by_alias=True), ensure_ascii=False, indent=2)
        (layout_dir / "layout.json").write_text(payload, encoding="utf-8")

    def delete_layout(self, layout_id: str) -> None:
        try:
            layout_dir = self._layout_dir(layout_id)
        except InvalidLayoutIdError:
            # 存在しないidの削除が無害なno-opであるのと同じ扱いにする
            # (不正なidだけを特別扱いして情報を漏らさない)。
            return
        if layout_dir.exists():
            shutil.rmtree(layout_dir)

    def load_status(self) -> StatusSnapshot:
        data = json.loads(self._status_path.read_text(encoding="utf-8"))
        return StatusSnapshot.model_validate(data)

    def save_status(self, status: StatusSnapshot) -> None:
        payload = json.dumps(status.model_dump(by_alias=True, mode="json"), ensure_ascii=False, indent=2)
        self._status_path.write_text(payload, encoding="utf-8")

    def load_tag_mappings(self) -> TagMappingSet:
        data = json.loads(self._tag_mappings_path.read_text(encoding="utf-8"))
        return TagMappingSet.model_validate(data)

    def save_tag_mappings(self, mapping_set: TagMappingSet) -> None:
        payload = json.dumps(mapping_set.model_dump(by_alias=True), ensure_ascii=False, indent=2)
        self._tag_mappings_path.write_text(payload, encoding="utf-8")

    def _layout_dir(self, layout_id: str) -> Path:
        """layout_idからキャンバスのディレクトリパスを組み立てる。

        layout_idはURLパス/クエリパラメータやJSONボディ(layout.id、
        original_id)経由で外部から渡ってくる文字列で、`../`や絶対パスを
        混ぜることでlayouts_dir外の任意の場所への書き込み・削除・読み取り
        を狙うパストラバーサル攻撃が可能だった(実際に検証済み)。
        `LayoutMeta.id`のスキーマ検証(安全な文字種のみ許可)が主な防御だが、
        URLパス/クエリ経由のlayout_id(スキーマを通らない)への防御として、
        ここでも解決後のパスがlayouts_dirの直下1階層に収まっているかを
        必ず確認する。"""
        try:
            candidate = (self._layouts_dir / layout_id).resolve()
        except (OSError, ValueError) as exc:
            # 埋め込みNUL文字などパスとして解決できない文字列が来た場合も
            # 500にせず、他の不正なidと同じ扱いにする。
            raise InvalidLayoutIdError(layout_id) from exc
        if candidate.parent != self._layouts_dir.resolve():
            raise InvalidLayoutIdError(layout_id)
        return candidate

    def _layout_path(self, layout_id: str) -> Path:
        try:
            layout_dir = self._layout_dir(layout_id)
        except InvalidLayoutIdError as exc:
            raise LayoutFileNotFoundError(layout_id) from exc
        path = layout_dir / "layout.json"
        if not path.exists():
            raise LayoutFileNotFoundError(layout_id)
        return path
