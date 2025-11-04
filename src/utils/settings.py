
import json
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from src.db import database, crud
from sqlalchemy.orm import Session

# ======================================================================================
# DATA MODELS
# ======================================================================================

class JiraModule(BaseModel):
    name: str
    url: HttpUrl
    isEnabled: bool

class LlmMonitoringSettings(BaseModel):
    webhookUrl: Optional[HttpUrl] = None
    apiKey: Optional[str] = None
    forwardUrl: Optional[str] = None
    proxyName: Optional[str] = None
    proxyPasswd: Optional[str] = None
    analyzedLogPath: Optional[str] = None
    analyzedLogMaxNumber: Optional[int] = None
    monitoringCycle: Optional[int] = None
    pendingTimeout: Optional[int] = None
    bertTimeout: Optional[int] = None
    llmTimeout: Optional[int] = None
    toolTimeout: Optional[int] = None

class BertSettings(BaseModel):
    url: Optional[HttpUrl] = None

class JiraSettings(BaseModel):
    url: Optional[HttpUrl] = None
    username: Optional[str] = None
    password: Optional[str] = None
    project: Optional[str] = None
    keywords: Optional[List[str]] = []

class OllamaSettings(BaseModel):
    url: Optional[HttpUrl] = None
    model: Optional[str] = None
    timeout: int = 0

class SambaSettings(BaseModel):
    id: str
    address: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

# ======================================================================================
# SETTINGS ACCESS FUNCTIONS
# ======================================================================================

# --- Generic Setting Get/Set --- 
def get_setting(category: str, key: str, default_value = None, db: Session = None):
    if db is None:
        db = database.get_db_session()
    kv_pair = crud.get_key_value(db, category=category, key=key)
    return kv_pair.value if kv_pair else default_value

def set_setting(category: str, key: str, value, db: Session = None):
    if db is None:
        db = database.get_db_session()
    crud.set_key_value(db, category=category, key=key, value=value)

# --- Jira Modules ---
def get_jira_modules(db: Session = None) -> List[JiraModule]:
    modules_json = get_setting("settings", "jira-modules", db=db)
    if modules_json:
        return [JiraModule.parse_raw(m) for m in json.loads(modules_json)]
    return []

def save_jira_modules(modules: List[JiraModule], db: Session = None):
    modules_str = json.dumps([m.json() for m in modules])
    set_setting("settings", "jira-modules", modules_str, db=db)

# --- LLM Monitoring ---
def get_llm_monitoring_settings(db: Session = None) -> LlmMonitoringSettings:
    settings_json = get_setting("settings", "llm-monitoring", db=db)
    return LlmMonitoringSettings.parse_raw(settings_json) if settings_json else LlmMonitoringSettings()

def save_llm_monitoring_settings(settings: LlmMonitoringSettings, db: Session = None):
    set_setting("settings", "llm-monitoring", settings.json(), db=db)

# --- Bert Settings ---
def get_bert_settings(db: Session = None) -> BertSettings:
    settings_json = get_setting("settings", "bert", db=db)
    return BertSettings.parse_raw(settings_json) if settings_json else BertSettings()

def save_bert_settings(settings: BertSettings, db: Session = None):
    set_setting("settings", "bert", settings.json(), db=db)

# --- Jira Settings ---
def get_jira_settings(db: Session = None) -> JiraSettings:
    settings_json = get_setting("settings", "jira", db=db)
    return JiraSettings.parse_raw(settings_json) if settings_json else JiraSettings()

def save_jira_settings(settings: JiraSettings, db: Session = None):
    set_setting("settings", "jira", settings.json(), db=db)

# --- Ollama Settings ---
def get_ollama_settings(db: Session = None) -> OllamaSettings:
    settings_json = get_setting("settings", "ollama", db=db)
    return OllamaSettings.parse_raw(settings_json) if settings_json else OllamaSettings()

def save_ollama_settings(settings: OllamaSettings, db: Session = None):
    set_setting("settings", "ollama", settings.json(), db=db)

# --- Samba Settings ---
def get_samba_settings(db: Session = None) -> List[SambaSettings]:
    settings_json = get_setting("settings", "samba", db=db)
    if settings_json:
        list_of_json_strings = json.loads(settings_json)
        return [SambaSettings.parse_raw(s) for s in list_of_json_strings]
    return []

def save_samba_settings(settings: List[SambaSettings], db: Session = None):
    settings_json = json.dumps([s.json() for s in settings])
    set_setting("settings", "samba", settings_json, db=db)

# --- Ollama Models Utility ---
def get_ollama_models() -> List[str]:
    from src.helper.Ollama import get_modes
    models = get_modes()
    return sorted(models)
