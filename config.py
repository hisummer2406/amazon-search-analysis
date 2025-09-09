from pydantic_settings import BaseSettings


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

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 3 * 1024 * 1024 * 1024  # 3GB for large files

    # 批处理配置
    BATCH_SIZE: int = 5000

    # Admin配置密钥：
    # python -c "import secrets; print(secrets.token_urlsafe(32))"
    ADMIN_SECRET_KEY: str

    # 多核处理配置
    MAX_WORKERS: int = 2  # 最大工作进程数
    MULTIPROCESSING_THRESHOLD_MB: float = 100.0  # 使用多进程的文件大小阈值(MB)
    FILE_SPLIT_LINES: int = 50000  # 文件分块行数

    # 数据库连接优化配置
    DB_POOL_SIZE: int = 10  # 连接池大小
    DB_MAX_OVERFLOW: int = 20  # 最大溢出连接
    DB_POOL_TIMEOUT: int = 30  # 连接超时时间（秒）
    DB_POOL_RECYCLE: int = 3600  # 连接回收时间
    DB_POOL_PRE_PING: bool = True  # 启用连接预检

    # 查询优化配置
    DB_ECHO: bool = False  # 生产环境关闭SQL日志
    DB_QUERY_TIMEOUT: int = 30  # 30秒查询超时

    class Config:
        env_file = ".env"
        extra = "ignore"


# 创建设置实例
settings = Settings()
