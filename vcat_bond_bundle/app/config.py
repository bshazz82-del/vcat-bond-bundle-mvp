from __future__ import annotations
import os
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="sqlite:///./vcat_bond_bundle.db")
    STORAGE_ROOT: str = Field(default=os.getenv("STORAGE_ROOT", os.path.join(os.getcwd(), "data")))

    STRIPE_SECRET_KEY: str = Field(default="")
    STRIPE_PRICE_ID: str = Field(default="")
    STRIPE_WEBHOOK_SECRET: str = Field(default="")

    DEFAULT_RETENTION_DAYS: int = Field(default=30)

    AI_API_KEY: str = Field(default="")
    LLM_MODEL_NAME: str = Field(default="gpt-3.5-turbo")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
