import json
from pathlib import Path

from schemas.api_config import ApiConfig

API_CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "sample" / "api_config.json"


class ApiConfigRepository:
    def __init__(self, path: Path = API_CONFIG_PATH) -> None:
        self._path = path

    def load(self) -> ApiConfig:
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return ApiConfig.model_validate(data)

    def save(self, config: ApiConfig) -> None:
        payload = json.dumps(config.model_dump(by_alias=True), ensure_ascii=False, indent=2)
        self._path.write_text(payload, encoding="utf-8")
