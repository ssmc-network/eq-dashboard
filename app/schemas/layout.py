from pydantic import BaseModel, ConfigDict, Field


class LayoutItem(BaseModel):
    """フロア上に配置される装置図形。タグ経由で状態と紐づく。"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    label: str
    x: int
    y: int
    w: int
    h: int
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
    items: list[LayoutItem] = []
