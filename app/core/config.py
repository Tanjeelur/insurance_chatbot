import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Insurance Document Analyzer"
    PROJECT_DESCRIPTION: str = "Analyze insurance documents and answer coverage questions"
    PROJECT_VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Model Configuration
    OPENAI_MODEL: str = "gpt-4o-mini"
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()