import logging
import time

from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings

logger = logging.getLogger(__name__)

"""SQLAlchemy 2.0 数据库模型基类"""


class Base(DeclarativeBase):
    metadata = MetaData(schema=settings.DATABASE_SCHEMA)


"""数据库连接配置"""
# 同步数据引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # 自动检测并重置失效连接
    echo=settings.DEBUG,
    connect_args={
        "options": "-c timezone=Asia/Shanghai"
    }
)

# 会话工厂
SessionFactory = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)

# 异步数据引擎
async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # 自动检测并重置失效连接
    echo=settings.DEBUG,
    connect_args={
        "server_settings": {
            "timezone": "Asia/Shanghai"
        }
    }
)

# 异步会话工厂
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # 异步会话默认不自动 flush
    autocommit=False,
)


# ========================================
# 慢查询日志配置 (同步引擎)
# ========================================
SLOW_QUERY_THRESHOLD = 1.0  # 超过 1 秒记录为慢查询


@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """记录查询开始时间"""
    context._query_start_time = time.time()


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """查询结束后记录慢查询"""
    total = time.time() - context._query_start_time
    if total > SLOW_QUERY_THRESHOLD:
        # 截断过长的 SQL 语句
        sql_preview = statement[:200] + "..." if len(statement) > 200 else statement
        logger.warning(
            f"慢查询检测 ({total:.2f}s): {sql_preview}"
        )


# 获取同步数据库会话 (FastAPI 依赖注入)
def get_db():
    """同步数据库会话生成器 - 用于 FastAPI Depends"""
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


# 异步数据库会话 (FastAPI 依赖注入)
async def get_async_db():
    """异步数据库会话生成器 - 用于 FastAPI Depends"""
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            # async with 会自动关闭，这里不需要显式 close
            pass
