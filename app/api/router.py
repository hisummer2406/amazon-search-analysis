from fastapi import APIRouter

from app.api.analysis_api import analysis_router
from app.api.upload_api import upload_router
from app.api.user_api import user_router
from app.api.auth_api import auth_router

api_router = APIRouter(prefix="/api" , tags=["API"])

# 认证路由
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["认证"]
)

api_router.include_router(
    analysis_router,
    prefix="/analysis",
    tags=["数据分析"]
)

api_router.include_router(
    upload_router,
    prefix="/upload",
    tags=["数据上传"]
)

api_router.include_router(
    user_router,
    prefix="/user",
    tags=["用户中心"]
)