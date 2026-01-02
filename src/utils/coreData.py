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
    PREPARING_LOG = (5, "下载解压日志")
    MCP_CONNECTING = (6, "等待连接MCP服务")
    NOT_ANALYZE_PERFORMANCE = (92, "performance的票不用分析")
    NOT_ANALYZE_CLONE = (93, "clone的票不用分析")
    NOT_ANALYZE_TRANSFER = (94, "不还没有分析，票已经被转走")
    NOT_ANALYZE_NOT_SDK_PROJECT = (95, "不是SDK项目，不需要分析")
    NOT_ANALYZE_LOG_NULL = (96, "没有日志，不需要分析")
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

class CoreDataMain(BaseModel):

    id: str = ""
    created_at: float = 0
    status: int = 0
    exception_string: str = ""
    is_bert: bool = False
    bert_component: str = ""
    bert_correct: int = 0
    bert_start: float = 0
    bert_end: float = 0

    class Config:
        from_attributes = True

class CoreDataSub(BaseModel):

    id: int = -1
    # main_id = Column(String, default="")
    main_id: str = ""
    status: int = 0
    exception_string: str = ""
    is_analyzed: bool = False
    component_of_tool: str = ""
    tool_name: str = ""
    analyze_start: float = 0
    analyze_end: float = 0

    llm_name: str = ""
    llm_start: float = 0
    llm_end: float = 0
    llm_success: bool = False
    llm_tokens: int = 0

    tool_llm_name: str = ""
    tool_llm_tokens: int = 0
    tool_llm_tag: str = ""

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

def get_core_data_main(key: str, db:Session) -> CoreDataMain:
    db_data = crud.get_core_data_main(db, id=key)
    if db_data:
        return CoreDataMain.model_validate(db_data)
    return CoreDataMain()

def save_core_data_main(key: str, data: CoreDataMain, db:Session) -> CoreDataMain:
    db_core_data = crud.get_core_data_main(db, id=key)

    # Pydantic V2 uses model_dump, ensure your Pydantic version is up to date
    update_data_dict = data.model_dump(exclude_unset=True, by_alias=False)

    if db_core_data:
        # Update existing
        for field, value in update_data_dict.items():
            setattr(db_core_data, field, value)
        saved_db_data = crud.update_core_data_main(db, core_data=db_core_data)
    else:
        # Create new
        new_data = models.CoreDataMain(**update_data_dict)
        saved_db_data = crud.create_core_data_main(db, core_data=new_data)

    return CoreDataMain.model_validate(saved_db_data)

def get_core_data_sub(key: int, db:Session) -> CoreDataSub:
    """Fetches core data for a given key and returns it as a Pydantic model."""
    db_data = crud.get_core_data_sub(db, id=key)
    if db_data:
        return CoreDataSub.model_validate(db_data)
    return CoreDataSub()

def save_core_data_sub(data: CoreDataSub, db:Session) -> CoreDataSub:
    """Saves core data for a given key and returns the saved data as a Pydantic model."""
    db_core_data = crud.get_core_data_sub(db, id=data.id)

    # Pydantic V2 uses model_dump, ensure your Pydantic version is up to date
    update_data_dict = data.model_dump(exclude_unset=True, by_alias=False)

    if db_core_data:
        # Update existing
        for field, value in update_data_dict.items():
            setattr(db_core_data, field, value)
        saved_db_data = crud.update_core_data_sub(db, core_data=db_core_data)
    else:
        # Create new
        if 'id' in update_data_dict:
            del update_data_dict['id']
        update_data_dict['main_id'] = data.main_id
        new_data = models.CoreDataSub(**update_data_dict)
        saved_db_data = crud.create_core_data_sub(db, core_data=new_data)

    return CoreDataSub.model_validate(saved_db_data)

def get_latest_core_data_sub_by_main_id(db: Session, main_id: str) -> models.CoreDataSub | None:
    return crud.get_latest_core_data_sub_by_main_id(db, main_id)

def get_latest_core_data_sub_by_main_id_ex(db: Session, main_id: str) -> models.CoreDataSub | None:
    return crud.get_latest_core_data_sub_by_main_id_ex(db, main_id)

def get_core_data_sub_by_main_id(db: Session, main_id: str) -> list[models.CoreDataSub] | None:
    return crud.get_core_data_sub_by_main_id(db, main_id)

def get_active_core_data(db: Session = None) -> list[models.CoreDataMain]:
    return crud.get_active_core_data(db)

def get_all_core_data(db: Session = None) -> list[models.CoreDataMain]:
    return crud.get_all_core_data(db)

def get_core_data_by_date_range(start_ts: float, end_ts: float, db: Session = None) -> list[models.CoreDataMain]:
    return crud.get_core_data_by_date_range(db, start_ts=start_ts, end_ts=end_ts)

def get_core_data_for_bert_correct(db: Session = None) -> list[models.CoreDataMain]:
    return crud.get_core_data_for_bert_correct(db)

def get_core_data_berted(db: Session = None) -> list[models.CoreDataMain]:
    return crud.get_core_data_berted(db)
