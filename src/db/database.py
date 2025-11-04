from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextvars import ContextVar
from typing import Union
from src.utils.config import settings as config
from contextlib import contextmanager

SQLALCHEMY_DATABASE_URL = f"postgresql://{config.POSTGRESSQL_USERNAME}:{config.POSTGRESSQL_PASSWORD}@{config.POSTGRESSQL_HOST}/naispilot"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Context variable to hold the database session
db_session_context: ContextVar[Union[sessionmaker, None]] = ContextVar("db_session_context", default=None)

def get_db_session():
    """Retrieves the database session from the context variable."""
    session = db_session_context.get()
    if session is None:
        raise Exception("Database session not found in context. Ensure the middleware is installed.")
    return session

# The old dependency function, kept for reference but will be phased out.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def standalone_session():
    """
    Provide a transactional scope around a series of operations for standalone scripts.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
