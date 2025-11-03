
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ENV = os.getenv("APP_ENV", "dev")
env_files = (".env", f".env.{APP_ENV}")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_files, env_file_encoding='utf-8', extra='ignore')

    JIRA_TIMEOUT: int = 3
    JIRA_MAX_RETRIES: int = 2

    JIRA_VERSION: int = 2
    JIRA_CUSTOM_FIELD_LINK_TO_PATH: str = ""
    JIRA_CUSTOM_FIELD_PRODUCT_VERSION: str = ""
    JIRA_CUSTOM_FIELD_REQ_BY_CUSTOMER:str = ""

settings = Settings()
