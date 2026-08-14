import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# idはファイルシステムのディレクトリ名として直接使われる(JsonStatusProvider)。
# `/`や`..`、絶対パスを許すとパストラバーサル(意図しないパス配下への
# 書き込み・削除・読み取り)になるため、安全な文字種のみに制限する。
_SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class LayoutItem(BaseModel):
    """フロア上に配置される図形。`type="equipment"`はタグ経由で状態と紐づく装置、
    `type="divider"`は部屋の区切りなどを表す線(装置ボックスの仕組みをそのまま
    再利用した細い矩形。稼働状態を持たず、独自の描画モデルは持たない)。
    既存の保存済みJSONには`type`フィールドが無いため、デフォルトで`equipment`
    として後方互換に読み込む。"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(min_length=1)
    label: str
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(gt=0)
    h: int = Field(gt=0)
    tag_id: str = Field(alias="tagId")
    type: Literal["equipment", "divider"] = "equipment"

    @model_validator(mode="after")
    def _divider_has_no_tag(self) -> "LayoutItem":
        if self.type == "divider" and self.tag_id:
            raise ValueError("区切り線にはtagIdを設定できません。")
        return self


class LayoutMeta(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    width: int = Field(gt=0)
    height: int = Field(gt=0)

    @field_validator("id")
    @classmethod
    def _id_must_be_filesystem_safe(cls, value: str) -> str:
        if not _SAFE_ID_PATTERN.match(value):
            raise ValueError("idには英数字・ハイフン・アンダースコアのみ使用できます。")
        return value


class LayoutDefinition(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: str = Field(alias="schemaVersion")
    layout: LayoutMeta
    items: list[LayoutItem] = []

    @model_validator(mode="after")
    def _no_duplicate_tag_ids(self) -> "LayoutDefinition":
        seen: set[str] = set()
        for item in self.items:
            if not item.tag_id:
                continue
            if item.tag_id in seen:
                raise ValueError(f"tagId「{item.tag_id}」が複数の装置で重複しています。")
            seen.add(item.tag_id)
        return self
