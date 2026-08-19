from functools import lru_cache
import os
from pathlib import Path
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Excel Workflow Platform"
    environment: str = "development"
    database_url: str = "sqlite:///./excel_workflow.db"
    upload_dir: str = "./data/uploads"
    output_dir: str = "./data/outputs"
    frontend_dist: str = "./frontend/dist"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context) -> None:
        base_dir = application_dir()
        data_dir = Path(os.getenv("EXCEL_WORKFLOW_DATA_DIR", str(base_dir / "data")))
        if not data_dir.is_absolute():
            data_dir = base_dir / data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        if self.database_url.startswith("sqlite:///./"):
            self.database_url = f"sqlite:///{data_dir / self.database_url.removeprefix('sqlite:///./')}"
        self.upload_dir = str(data_dir / self.upload_dir.removeprefix("./"))
        self.output_dir = str(data_dir / self.output_dir.removeprefix("./"))
        self.frontend_dist = str(base_dir / self.frontend_dist)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
