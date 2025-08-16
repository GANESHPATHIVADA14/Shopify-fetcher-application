# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator, PostgresDsn, AnyUrl
from typing import Optional

class Settings(BaseSettings):
    # Core app settings
    APP_ENV: str = "development"

    # Database settings
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None # <-- Make it an integer for better validation
    DB_NAME: Optional[str] = None
    
    # This field will be *computed* from the others, not read from .env
    DATABASE_URL: Optional[str] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            # If DATABASE_URL is already provided in .env, use it
            return v
        
        # Otherwise, build it from the component parts
        user = values.get("DB_USER")
        password = values.get("DB_PASSWORD")
        host = values.get("DB_HOST")
        port = values.get("DB_PORT")
        db_name = values.get("DB_NAME")
        
        # Only assemble if all parts are present
        if all([user, password, host, port, db_name]):
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
        return None # Return None if parts are missing

    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    SERPAPI_KEY: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')


settings = Settings()