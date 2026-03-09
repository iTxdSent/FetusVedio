from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "胎儿超声视频流实时解译系统 Demo"
    api_prefix: str = "/api/v1"
    database_url: str = f"sqlite:///{Path(__file__).resolve().parents[2] / 'data' / 'app.db'}"
    stream_fps: int = 30
    jpeg_quality: int = 85
    capture_device_index: int = 0
    synthetic_width: int = 960
    synthetic_height: int = 540
    cors_allow_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    local_video_upload_dir: str = str(Path(__file__).resolve().parents[2] / "data" / "uploads")
    snapshot_root_dir: str = str(Path(__file__).resolve().parents[2] / "data" / "snapshots")
    model_provider_backend: str = "mock"
    auto_capture_consecutive_frames: int = 2
    auto_capture_cooldown_sec: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
