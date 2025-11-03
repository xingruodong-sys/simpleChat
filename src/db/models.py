from sqlalchemy import Column, String, Integer, Float, Boolean
from src.db.database import Base, engine

class CoreData(Base):
    __tablename__ = "core_data"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(Float, default=0)
    status = Column(Integer, default=0, index=True)
    exception_string = Column(String, default="")

    isBert = Column(Boolean, default=False)
    bertComponent = Column(String, default="")
    bertStart = Column(Float, default=0)
    bertEnd = Column(Float, default=0)
    bertCorrect = Column(Integer, default=0)

    isAnalyzed = Column(Boolean, default=False)
    toolName = Column(String, default="")
    analyzeStart = Column(Float, default=0)
    analyzeEnd = Column(Float, default=0)

    llmName = Column(String, default="")
    llmStart = Column(Float, default=0)
    llmEnd = Column(Float, default=0)
    llmSuccess = Column(Boolean, default=False)
    llmTokens = Column(Integer, default=0)


class KeyValue(Base):
    __tablename__ = "key_value_store"

    category = Column(String, primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(String)


# Base.metadata.create_all(bind=engine)