from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextvars import ContextVar
from contextlib import contextmanager
from typing import Generator, Union, Optional
from src.utils.config import settings as config


# ============================================================
# 数据库连接管理模块（可复用）
# ============================================================

class DatabaseManager:
    """通用 SQLAlchemy 数据库管理类，可复用于多个项目或数据库"""
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or self._build_default_url()
        self.engine = create_engine(self.db_url, pool_pre_ping=True, pool_size=50, max_overflow=100, pool_recycle=1800, pool_timeout=30)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.Base = declarative_base()

        # 当前上下文的 session
        self._session_context: ContextVar[Optional[sessionmaker]] = ContextVar(
            "db_session_context", default=None
        )

    def _build_default_url(self) -> str:
        """根据全局配置构建默认数据库连接字符串"""
        return (
            f"postgresql://{config.POSTGRESSQL_USERNAME}:"
            f"{config.POSTGRESSQL_PASSWORD}@"
            f"{config.POSTGRESSQL_HOST}:"
            f"{config.POSTGRESSQL_PORT}/naispilot"
        )

    # ---------- FastAPI / async 框架依赖 ----------
    def get_db(self) -> Generator:
        """传统依赖注入方式，用于 FastAPI 等框架"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # ---------- 独立上下文（适用于脚本或后台任务） ----------
    @contextmanager
    def standalone_session(self):
        """提供一个独立 session 上下文"""
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ---------- 动态切换数据库 ----------
    def switch_database(self, new_url: str):
        """在运行时切换数据库"""
        self.db_url = new_url
        self.engine.dispose()  # 关闭旧连接池
        self.engine = create_engine(new_url, pool_pre_ping=True)
        self.SessionLocal.configure(bind=self.engine)


# ============================================================
# 实例化一个全局 DatabaseManager
# ============================================================

db_manager = DatabaseManager()

# 便捷别名，兼容旧代码
Base = db_manager.Base
engine = db_manager.engine
get_db = db_manager.get_db
standalone_session = db_manager.standalone_session
