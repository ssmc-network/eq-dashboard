from pydantic import BaseModel, ConfigDict, Field


class LayoutShape(BaseModel):
    """フロア構造を表す矩形図形(壁・ゾーンなど、状態を持たない)。"""

    id: str
    label: str
    x: int
    y: int
    w: int
    h: int


class LayoutDevice(BaseModel):
    """フロア上の座標に配置される装置ピン。タグ経由で状態と紐づく。"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    label: str
    x: int
    y: int
    tag_id: str = Field(alias="tagId")


class LayoutMeta(BaseModel):
    id: str
    name: str
    width: int
    height: int


class LayoutDefinition(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: str = Field(alias="schemaVersion")
    layout: LayoutMeta
    shapes: list[LayoutShape] = []
    devices: list[LayoutDevice] = []
