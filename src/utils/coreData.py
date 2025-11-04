from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_snake
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
    model_config = ConfigDict(
        alias_generator=to_snake,
        from_attributes=True,
        populate_by_name=True,
    )

    id: str = ""
    created_at: float = 0
    status: int = 0
    exception_string: str = ""

    is_bert: bool = False
    bert_component: str = ""
    bert_start: float = 0
    bert_end: float = 0
    bert_correct: bool = True

    is_analyzed: bool = False
    tool_name: str = ""
    analyze_start: float = 0
    analyze_end: float = 0

    llm_name: str = ""
    llm_start: float = 0
    llm_end: float = 0
    llm_success: bool = False
    llm_tokens: int = 0

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

def get_core_data(key: str) -> Optional[CoreData]:
    """Fetches core data for a given key and returns it as a Pydantic model."""
    db = database.get_db_session()
    db_data = crud.get_core_data(db, id=key)
    if db_data:
        return CoreData.model_validate(db_data)
    return None

def save_core_data(db: Session, key: str, data: CoreData) -> CoreData:
    """Saves core data for a given key and returns the saved data as a Pydantic model."""
    db = database.get_db_session()
    db_core_data = crud.get_core_data(db, id=key)
    
    # Dump the pydantic model to a dict with snake_case keys, suitable for the database model
    update_data_dict = data.model_dump(exclude_unset=True, by_alias=True)

    if db_core_data:
        # Update existing
        for field, value in update_data_dict.items():
            setattr(db_core_data, field, value)
        saved_db_data = crud.update_core_data(db, core_data=db_core_data)
    else:
        # Create new
        # On creation, we can use the full dict
        create_data_dict = data.model_dump(by_alias=True)
        new_data = models.CoreData(**create_data_dict)
        saved_db_data = crud.create_core_data(db, core_data=new_data)
    
    return CoreData.model_validate(saved_db_data)

# def save_to_not_analyzed(table, key):
#     redis_client.lpush(table, key)

def get_active_core_data() -> list[models.CoreData]:
    """Retrieves all active tasks from the database."""
    db = database.get_db_session()
    active_data = crud.get_active_core_data(db)
    return [CoreData.model_validate(item) for item in active_data]

def get_all_core_data() -> list[models.CoreData]:
    """Retrieves all tasks from the database."""
    all_data = crud.get_all_core_data(db)
    return [CoreData.model_validate(item) for item in all_data]

def get_core_data_by_date_range(start_ts: float, end_ts: float) -> list[models.CoreData]:
    """Retrieves tasks from the database within a date range."""
    db = database.get_db_session()
    ranged_data = crud.get_core_data_by_date_range(db, start_ts=start_ts, end_ts=end_ts)
    return [CoreData.model_validate(item) for item in ranged_data]
