from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service: str = "eq-dashboard"
    tz: str = "Asia/Tokyo"
    loglevel: str = "INFO"
    debug: bool = False


settings = Settings()
