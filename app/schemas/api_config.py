from pydantic import BaseModel, ConfigDict, Field

AUTH_TYPES = ("none", "api_key", "bearer")


class ApiConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    base_url: str = Field(alias="baseUrl", default="")
    auth_type: str = Field(alias="authType", default="none")
    api_key_header: str = Field(alias="apiKeyHeader", default="X-API-Key")
    credential: str = Field(default="")
