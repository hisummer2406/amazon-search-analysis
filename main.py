import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.api.router import api_router
from config import settings
from database import engine, async_engine
from app.admin.admin_site import site
from monitoring import SystemMonitor
from app.middleware.auth_middleware import AdminAuthMiddleware


# 配置应用日志，每天自动生成新文件
def configure_logging():
    import logging.handlers
    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.handlers.TimedRotatingFileHandler(
                "logs/app.log", when="midnight", backupCount=7, encoding="utf-8"
            ),
            logging.StreamHandler(),
        ],
    )
    # 控制台输出
    logging.StreamHandler()

configure_logging()
logger = logging.getLogger(__name__)

def init_upload_dir():
    try:
        # 确保上传目录存在
        os.makedirs(f"{settings.UPLOAD_DIR}/daily", exist_ok=True)
        os.makedirs(f"{settings.UPLOAD_DIR}/weekly", exist_ok=True)
        logger.info("✅ 上传目录初始化成功")
    except Exception as e:
        logger.error(f"❌ 上传目录初始化失败: {e}")


"""异步上下文管理器"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时执行
    logger.info(f"🚀 {settings.APP_NAME} v{settings.VERSION} 启动中...")
    logger.info(f"📊 数据库Schema: {settings.DATABASE_SCHEMA}")
    logger.info(f"📁 上传目录: {settings.UPLOAD_DIR}")
    logger.info(f"⚙️ 批处理大小: {settings.BATCH_SIZE}")
    logger.info(f"🔍 查询天数限制: {settings.QUERY_DAYS_LIMIT}")

    # 初始化上传目录
    init_upload_dir()

    # 检查数据库连接
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("✅ 同步数据库连接测试成功")
    except Exception as e:
        logger.error(f"❌ 同步数据库连接测试失败: {e}")

    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ 异步数据库连接测试成功")
    except Exception as e:
        logger.error(f"❌ 异步数据库连接测试失败: {e}")

    logger.info("🎉 应用启动完成，准备接收请求")

    yield

    # ==================== 关闭事件 ====================
    logger.info("🛑 应用正在关闭...")

    # 关闭数据库连接
    try:
        engine.dispatch()
        logger.info("✅ 同步数据库连接关闭成功")
    except Exception as e:
        logger.error(f"❌ 同步数据库连接关闭失败: {e}")

    try:
        await async_engine.dispose()
        logger.info("✅ 异步数据库连接关闭成功")
    except Exception as e:
        logger.error(f"❌ 异步数据库连接关闭失败: {e}")

    logger.info("👋 应用已安全关闭")

"""创建FastAPI应用"""
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="亚马逊搜索词分析工具",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan  # 使用新的生命周期管理
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")
# 挂载后台管理系统
site.mount_app(app)
#注册API路由
app.include_router(api_router)

app.add_middleware(AdminAuthMiddleware)

@app.get("/")
async def root():
    return RedirectResponse(url="/admin/login")

@app.get("/health")
async def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": {
                "sync": "healthy",
                "async": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        return {"status": "unhealthy", "error": str(e)}

# 集成到FastAPI应用
@app.get("/api/monitoring/metrics")
async def get_system_metrics():
    """获取系统监控指标"""
    monitor = SystemMonitor()
    metrics = await monitor.collect_metrics()
    summary = monitor.get_performance_summary()

    return {
        'current_metrics': metrics,
        'summary': summary,
        'status': 'healthy' if metrics['cpu']['total'] < 80 and metrics['memory']['percent'] < 80 else 'warning'
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
