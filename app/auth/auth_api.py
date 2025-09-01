# app/api/auth_api_simple.py
"""简化版认证API - 只提供登录功能"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.auth.simple_auth import simple_auth
from app.user.user_model import UserCenter

auth_router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@auth_router.post("/login")
async def login(login_data: LoginRequest):
    """用户登录"""
    try:
        result = await simple_auth.login(login_data.username, login_data.password)
        return {"status": 0, "msg": "登录成功", "data": result}
    except HTTPException as e:
        return {"status": 1, "msg": e.detail, "data": None}


@auth_router.get("/profile")
def get_profile(current_user: UserCenter = Depends(simple_auth.get_current_user)):
    """获取当前用户信息"""
    return {
        "status": 0,
        "msg": "获取成功",
        "data": {
            "id": current_user.id,
            "username": current_user.user_name,
            "is_super": current_user.is_super,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat()
        }
    }


@auth_router.post("/logout")
def logout(current_user: UserCenter = Depends(simple_auth.get_current_user)):
    """登出"""
    return {"status": 0, "msg": "登出成功"}