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
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

# 会话工厂
SessionFactory = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

# 异步数据引擎
async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

# 异步会话工厂
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

"""依赖注入函数"""

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