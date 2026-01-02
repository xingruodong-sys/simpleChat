from fastapi import APIRouter, Depends
from src.db.database import get_db
from sqlalchemy.orm import Session
from typing import List

# Import the data models and the manager functions from the new core module
from src.utils.settings import (
    get_jira_modules, save_jira_modules, JiraModule,
    get_llm_monitoring_settings, save_llm_monitoring_settings, LlmMonitoringSettings,
    get_bert_settings, save_bert_settings, BertSettings,
    get_jira_settings, save_jira_settings, JiraSettings,
    get_ollama_settings, save_ollama_settings, OllamaSettings,
    get_samba_settings, save_samba_settings, SambaSettings,
    get_ollama_models
)

# --- Router Initialization ---
router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)

# ======================================================================================
# API ENDPOINTS (Thin Wrappers around the Settings Manager)
# ======================================================================================

# --- Jira Modules ---
@router.get("/jira-modules", response_model=List[JiraModule])
async def get_jira_modules_endpoint(db: Session = Depends(get_db)):
    return get_jira_modules(db)

@router.post("/jira-modules")
async def save_jira_modules_endpoint(modules: List[JiraModule], db: Session = Depends(get_db)):
    save_jira_modules(modules, db)
    return {"status": "success"}

# --- LLM Monitoring ---
@router.get("/llm-monitoring", response_model=LlmMonitoringSettings)
async def get_llm_monitoring_settings_endpoint(db: Session = Depends(get_db)):
    return get_llm_monitoring_settings(db)

@router.post("/llm-monitoring")
async def save_llm_monitoring_settings_endpoint(settings: LlmMonitoringSettings,  db: Session = Depends(get_db)):
    save_llm_monitoring_settings(settings)
    return {"status": "success"}

# --- Bert Settings ---
@router.get("/bert", response_model=BertSettings)
async def get_bert_settings_endpoint(db: Session = Depends(get_db)):
    return get_bert_settings(db)

@router.post("/bert")
async def save_bert_settings_endpoint(settings: BertSettings, db: Session = Depends(get_db)):
    save_bert_settings(settings, db)
    return {"status": "success"}

# --- Jira Settings ---
@router.get("/jira", response_model=JiraSettings)
async def get_jira_settings_endpoint(db: Session = Depends(get_db)):
    return get_jira_settings(db)

@router.post("/jira")
async def save_jira_settings_endpoint(settings: JiraSettings, db: Session = Depends(get_db)):
    save_jira_settings(settings, db)
    return {"status": "success"}

# --- Ollama Settings ---
@router.get("/ollama", response_model=OllamaSettings)
async def get_ollama_settings_endpoint(db: Session = Depends(get_db)):
    return get_ollama_settings(db)

@router.post("/ollama")
async def save_ollama_settings_endpoint(settings: OllamaSettings, db: Session = Depends(get_db)):
    save_ollama_settings(settings, db)
    return {"status": "success"}

# --- Samba Settings ---
@router.get("/samba", response_model=List[SambaSettings])
async def get_samba_settings_endpoint(db: Session = Depends(get_db)):
    return get_samba_settings(db)

@router.post("/samba")
async def save_samba_settings_endpoint(settings: List[SambaSettings], db: Session = Depends(get_db)):
    save_samba_settings(settings, db)
    return {"status": "success"}

# --- Ollama Models Utility ---
@router.get("/models", response_model=List[str])
async def get_ollama_models_endpoint(db: Session = Depends(get_db)):
    return get_ollama_models(db)
    
