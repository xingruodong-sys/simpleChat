from pydantic import BaseModel
from enum import Enum
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from src.db import crud, models, database
# ======================================================================================
# Enum 
# ======================================================================================

class Status(Enum):
    NEW = (0, "新建")
    PENDING = (1, "等待上传日志")
    WATING_BERT = (2, "等待分析模块")
    WATING_LLM = (3, "等待LLM分析")
    WATING_TOOL = (4, "等待TOOL分析")
    EXCEPTION = (97, "异常")
    DONE_BERT = (98, "完成")
    DONE = (99, "完成")

    def __init__(self, code: int, description: str):
        self.code = code
        self.description = description

    @property
    def value(self) -> int:
        return self.code

    def __str__(self):
        return self.description

    def __int__(self):
        return self.code

# ======================================================================================
# DATA MODELS
# ======================================================================================

class CoreData(BaseModel):
    id: str = ""
    created_at: float = 0
    status: int = 0
    exception_string: str = ""

    isBert: bool = False
    bertComponent: str = ""
    bertStart: float = 0
    bertEnd: float = 0
    bertCorrect: bool = True

    isAnalyzed: bool = False
    toolName: str = ""
    analyzeStart: float = 0
    analyzeEnd: float = 0

    llmName: str = ""
    llmStart: float = 0
    llmEnd: float = 0
    llmSuccess: bool = False
    llmTokens: int = 0

    # model='qwen3:32b'
    # created_at='2025-10-05T08:10:20.541990235Z' 
    # done=True 
    # done_reason='stop' 
    # total_duration=2180758112 
    # load_duration=41696344 
    # prompt_eval_count=1168 
    # prompt_eval_duration=25449910 
    # eval_count=71 
    # eval_duration=2102751070 
    # message=Message(role='assistant', content='', thinking=None, images=None, tool_calls=[ToolCall(function=Function(name='analyze_route_log', arguments={'android_file_urls': ['1.txt', '1.txt'], 'dlt_file_urls': ['1.dlt'], 'jiraid': 'AINMASDK-3625', 'logtime': 'None', 'summary': '东南亚在线算路失败'}))])

# ======================================================================================
# SETTINGS ACCESS FUNCTIONS
# ======================================================================================

NO_LOG_KEY = "no_log_issues"
NOT_ANALYZED_KEY = "not_to_analyze_issues"
NOT_IN_T3000_KEY = "not_in_t3000_issues"

def get_core_data(key: str) -> Optional[models.CoreData]:
    """Fetches core data for a given key from the database."""
    db = database.get_db_session()
    return crud.get_core_data(db, id=key)

def save_core_data(db: Session, key: str, data: CoreData) -> models.CoreData:
    """Saves core data for a given key to the database."""
    db = database.get_db_session()
    db_core_data = crud.get_core_data(db, id=key)
    if db_core_data:
        # Update existing
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_core_data, field, value)
        return crud.update_core_data(db, core_data=db_core_data)
    else:
        # Create new
        new_data = models.CoreData(**data.model_dump())
        return crud.create_core_data(db, core_data=new_data)

# def save_to_not_analyzed(table, key):
#     redis_client.lpush(table, key)

def get_active_core_data() -> list[models.CoreData]:
    """Retrieves all active tasks from the database."""
    db = database.get_db_session()
    return crud.get_active_core_data(db)

def get_all_core_data() -> list[models.CoreData]:
    """Retrieves all tasks from the database."""
    db = database.get_db_session()
    return crud.get_all_core_data(db)

def get_core_data_by_date_range(start_ts: float, end_ts: float) -> list[models.CoreData]:
    """Retrieves tasks from the database within a date range."""
    db = database.get_db_session()
    return crud.get_core_data_by_date_range(db, start_ts=start_ts, end_ts=end_ts)
