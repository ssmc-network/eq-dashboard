from pydantic import BaseModel, ConfigDict, Field


class TagMapping(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tag_id: str = Field(alias="tagId")
    api_field: str = Field(alias="apiField")
    running_value: str = Field(alias="runningValue", default="")
    stopped_value: str = Field(alias="stoppedValue", default="")
    alarm_value: str = Field(alias="alarmValue", default="")


class TagMappingSet(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: str = Field(alias="schemaVersion")
    mappings: list[TagMapping]
