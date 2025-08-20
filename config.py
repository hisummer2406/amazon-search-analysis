from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str
    VERSION: str
    DEBUG: bool

    # 数据库配置: postgresql://[username]:[password]@[host]:[port]/[database_name]?[参数1]=[值1]&[参数2]=[值2]
    DATABASE_URL: str
    DATABASE_URL_ASYNC: str

    # 数据库Schema
    DATABASE_SCHEMA: str

    # Redis配置（用于异步任务）
    REDIS_URL: str

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 3 * 1024 * 1024 * 1024  # 3GB for large files

    # 批处理配置
    BATCH_SIZE: int = 10000  # 每批处理1万条记录
    MAX_WORKERS: int = 4  # 并发处理线程数

    # 查询限制
    QUERY_DAYS_LIMIT: int = 7  # 只查询最近7天数据

    # Admin配置密钥：
    # python -c "import secrets; print(secrets.token_urlsafe(32))"
    ADMIN_SECRET_KEY: str

    class Config:
        env_file = ".env"


# 创建设置实例
settings = Settings()

if __name__ == "__main__":
    print(os.getcwd())
    print(os.listdir())
