from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagMapping(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tag_id: str = Field(alias="tagId")
    api_field: str = Field(alias="apiField")
    running_value: str = Field(alias="runningValue", default="")
    stopped_value: str = Field(alias="stoppedValue", default="")
    alarm_value: str = Field(alias="alarmValue", default="")

    @field_validator("tag_id", "api_field")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("値を入力してください。")
        return value


class TagMappingSet(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: str = Field(alias="schemaVersion")
    mappings: list[TagMapping]
