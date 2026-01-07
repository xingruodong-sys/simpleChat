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

class StatisticsEffectiveIp(Base):
    __tablename__ = "statistics_effective_ip"
    
    TicketID = Column(String, primary_key=True, index=True)
    created_at = Column(String, default="")
    bert_component = Column(String, default="")
    ai_first_ana_start = Column(Float, default=0)
    create_at_to_ai_ana = Column(Float, default=0)
    manually_first_ana_start = Column(Float, default=0)
    create_at_to_manually_ana = Column(Float, default=0)
    integration = Column(String, default="")
    create_at_to_integration = Column(Float, default=0)
    reject = Column(String, default="")
    create_at_to_reject = Column(Float, default=0)
    resovled = Column(String, default="")
    create_at_to_resovled = Column(Float, default=0)
    tool_name = Column(String, default="")
    hmi_tag = Column(String, default="")

class StatisticsManualEfficiency(Base):
    __tablename__ = "statistics_manual_efficiency"
    
    TicketID = Column(String, primary_key=True, index=True)
    created_at = Column(String, default="")
    author = Column(String, default="")
    manually_first_ana_start = Column(Float, default=0)
    create_at_to_manually_ana = Column(Float, default=0)
    integration = Column(String, default="")
    create_at_to_integration = Column(Float, default=0)
    reject = Column(String, default="")
    create_at_to_reject = Column(Float, default=0)
    resovled = Column(String, default="")
    create_at_to_resovled = Column(Float, default=0)

class StatisticsBertCorrect(Base):
    __tablename__ = "statistics_bert_correct"
    
    id = Column(String, primary_key=True, index=True)
    bert_component = Column(String, default="")
    analyze_component = Column(String, default="")
    correct = Column(Boolean, default=False)
    manually_analyze = Column(Boolean, default=False)

class StatisticsBertHistory(Base):
    __tablename__ = "statistics_bert_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(Integer, default=0)
    daily_correct = Column(Integer, default=0)
    daily_error = Column(Integer, default=0)
    daily_rate = Column(Float, default=0.0)
    cumulative_correct = Column(Integer, default=0)
    cumulative_error = Column(Integer, default=0)
    cumulative_rate = Column(Float, default=0.0)

class StatisticsBertWeeklyHistory(Base):
    __tablename__ = "statistics_bert_weekly_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    week_start = Column(Float, default=0)
    week_end = Column(Float, default=0)
    week_start_str = Column(String, default="")
    week_end_str = Column(String, default="")
    weekly_correct = Column(Integer, default=0)
    weekly_error = Column(Integer, default=0)
    weekly_rate = Column(Float, default=0.0)
    cumulative_correct = Column(Integer, default=0)
    cumulative_error = Column(Integer, default=0)
    cumulative_rate = Column(Float, default=0.0)

Base.metadata.create_all(bind=engine)
