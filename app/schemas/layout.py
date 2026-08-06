from pydantic import BaseModel, ConfigDict, Field, model_validator


class LayoutItem(BaseModel):
    """フロア上に配置される装置図形。タグ経由で状態と紐づく。"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(min_length=1)
    label: str
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(gt=0)
    h: int = Field(gt=0)
    tag_id: str = Field(alias="tagId")


class LayoutMeta(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


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
