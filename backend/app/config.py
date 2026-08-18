from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Smart Attendance"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    SECRET_KEY: str = "change-this-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/attendance.db"

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = Path(__file__).resolve().parent.parent.parent / "data"
    MODELS_DIR: Path = Path(__file__).resolve().parent.parent.parent / "ai" / "models"

    FACE_MODEL: str = "buffalo_sc"
    DETECTION_THRESHOLD: float = 0.5
    RECOGNITION_THRESHOLD: float = 0.45
    LIVENESS_THRESHOLD: float = 0.3

    CAMERA_FPS: int = 30
    CAMERA_RESOLUTION: tuple = (1280, 720)
    MAX_FACES: int = 20

    ATTENDANCE_COOLDOWN_SECONDS: int = 300
    VERIFICATION_FRAMES: int = 3
    BUFFER_SIZE: int = 7

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
