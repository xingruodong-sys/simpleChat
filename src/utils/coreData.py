from pydantic import BaseModel
from enum import Enum
from src.db import crud, models, database
from sqlalchemy.orm import Session
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

    class Config:
        from_attributes = True

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

def get_core_data(key: str) -> CoreData:
    """Fetches core data for a given key and returns it as a Pydantic model."""
    db = database.get_db_session()
    db_data = crud.get_core_data(db, id=key)
    if db_data:
        return CoreData.model_validate(db_data)
    return CoreData()

def save_core_data(key: str, data: CoreData) -> CoreData:
    """Saves core data for a given key and returns the saved data as a Pydantic model."""
    db = database.get_db_session()
    db_core_data = crud.get_core_data(db, id=key)
    
    # Pydantic V2 uses model_dump, ensure your Pydantic version is up to date
    update_data_dict = data.model_dump(exclude_unset=True, by_alias=False)

    if db_core_data:
        # Update existing
        for field, value in update_data_dict.items():
            setattr(db_core_data, field, value)
        saved_db_data = crud.update_core_data(db, core_data=db_core_data)
    else:
        # Create new
        new_data = models.CoreData(**update_data_dict)
        saved_db_data = crud.create_core_data(db, core_data=new_data)
    
    return CoreData.model_validate(saved_db_data)

# def save_to_not_analyzed(table, key):
#     redis_client.lpush(table, key)

def get_active_core_data(db: Session = None) -> list[models.CoreData]:
    if db is None:
        db = database.get_db_session()
    return crud.get_active_core_data(db)

def get_all_core_data(db: Session = None) -> list[models.CoreData]:
    if db is None:
        db = database.get_db_session()
    return crud.get_all_core_data(db)

def get_core_data_by_date_range(start_ts: float, end_ts: float, db: Session = None) -> list[models.CoreData]:
    if db is None:
        db = database.get_db_session()
    return crud.get_core_data_by_date_range(db, start_ts=start_ts, end_ts=end_ts)
