from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DEBUG: bool = False

    UPLOAD_DIR: str = 'uploads'
    MAX_FILE_SIZE: int = 3 * 1024 * 1024 * 1024 #最大3G

    # pydantic_settings 从环境变量加载配置
    class Config:
        env_file = '.env'

# 加载配置
settings = Settings()

# 确保上传目录存在
os.makedirs(f"{settings.UPLOAD_DIR}/daily", exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/weekly", exist_ok=True)
os.makedirs("logs", exist_ok=True)

