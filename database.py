import logging

from sqlalchemy import create_engine, MetaData
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
)


# 获取同步数据库会话
def get_db():
    with SessionFactory() as session:
        try:
            yield session
        finally:
            session.close()


# 异步数据库会话
def get_async_db():
    with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            session.close()
