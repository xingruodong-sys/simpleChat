
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ENV = os.getenv("APP_ENV", "dev")
env_files = (".env", f".env.{APP_ENV}")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_files, env_file_encoding='utf-8', extra='ignore')

    JIRA_TIMEOUT: int = 3
    JIRA_MAX_RETRIES: int = 2

    JIRA_CUSTOM_FIELD_LINK_TO_PATH: str = "customfield_12010"
    JIRA_CUSTOM_FIELD_PRODUCT_VERSION: str = "customfield_12051"
    JIRA_CUSTOM_FIELD_REQ_BY_CUSTOMER:str = "customfield_10191"
    JIRA_CUSTOM_FIELD_FUNCTION_OWNER: str = "customfield_14311"

    POSTGRESSQL_USERNAME: str = "postgres"
    POSTGRESSQL_PASSWORD: str = "neuadminpostgreroot"
    POSTGRESSQL_HOST: str = ""
    POSTGRESSQL_PORT: str = ""

settings = Settings()
