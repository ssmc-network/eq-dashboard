from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StatusItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tag_id: str = Field(alias="tagId")
    value: str
    severity: str
    updated_at: datetime = Field(alias="updatedAt")


class StatusSnapshot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: str = Field(alias="schemaVersion")
    generated_at: datetime = Field(alias="generatedAt")
    statuses: list[StatusItem]
