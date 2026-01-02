from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey
from src.db.database import Base, engine

class CoreData(Base):
    __tablename__ = "core_data"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(Float, default=0)
    status = Column(Integer, default=0, index=True)
    exception_string = Column(String, default="")

    is_bert = Column(Boolean, default=False)
    bert_component = Column(String, default="")
    bert_start = Column(Float, default=0)
    bert_end = Column(Float, default=0)
    bert_correct = Column(Integer, default=0)

    is_analyzed = Column(Boolean, default=False)
    tool_name = Column(String, default="")
    analyze_start = Column(Float, default=0)
    analyze_end = Column(Float, default=0)

    llm_name = Column(String, default="")
    llm_start = Column(Float, default=0)
    llm_end = Column(Float, default=0)
    llm_success = Column(Boolean, default=False)
    llm_tokens = Column(Integer, default=0)


class KeyValue(Base):
    __tablename__ = "settings"

    category = Column(String, primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(String)

class CoreDataMain(Base):
    __tablename__ = "core_data_main"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(Float, default=0)
    status = Column(Integer, default=0, index=True)
    is_bert = Column(Boolean, default=False)
    bert_component = Column(String, default="")
    bert_correct = Column(Integer, default=0)
    bert_start = Column(Float, default=0)
    bert_end = Column(Float, default=0)

class CoreDataSub(Base):
    __tablename__ = "core_data_sub"

    id = Column(Integer, primary_key=True, index=True)
    # main_id = Column(String, default="")
    main_id = Column(String, ForeignKey("core_data_main.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Integer, default=0, index=True)
    exception_string = Column(String, default="")
    is_analyzed = Column(Boolean, default=False)
    component_of_tool = Column(String, default="")
    tool_name = Column(String, default="")
    analyze_start = Column(Float, default=0)
    analyze_end = Column(Float, default=0)

    llm_name = Column(String, default="")
    llm_start = Column(Float, default=0)
    llm_end = Column(Float, default=0)
    llm_success = Column(Boolean, default=False)
    llm_tokens = Column(Integer, default=0)

    tool_llm_name = Column(String, default="")
    tool_llm_tokens = Column(Integer, default=0)
    tool_llm_tag = Column(String, default="")

Base.metadata.create_all(bind=engine)