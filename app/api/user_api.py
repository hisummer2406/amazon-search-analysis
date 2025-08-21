import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from app.services.login_auth import auth_service
from app.dependencies.login_auth import get_current_user
from app.crud.user_crud import UserCenterCRUD
from app.schemas.user_schemas import (
    UserLoginResponse, UserCenterCreate, UserCenterUpdate
)

logger = logging.getLogger(__name__)

user_router = APIRouter()


@user_router.get("/list", response_model=Dict[str, Any])
async def get_users_list(
        page: int = Field(1, ge=1, description="页码"),
        per_page: int = Field(20, ge=1, le=100, description="每页数量"),
        user_name: Optional[str] = Field(None, description="搜索关键词"),
        is_active: Optional[bool] = Field(None, description="用户状态筛选"),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取用户列表 - 支持分页和搜索"""
    try:
        crud = UserCenterCRUD(db)
        result = crud.get_users_paginated(
            page=page,
            per_page=per_page,
            user_name=user_name,
            is_active=is_active
        )

        return {
            "status": 0,
            "msg": "获取成功",
            "data": {
                "items": result["items"],
                "count": result["total"],
                "page": result["page"],
                "perPage": result["per_page"],
                "totalPages": result["pages"]
            }
        }

    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户列表失败")


@user_router.post("/login", response_model=UserLoginResponse)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
) -> UserLoginResponse:
    """用户登录"""
    try:
        # 查询用户
        crud = UserCenterCRUD(db)
        user = crud.get_user_by_username(form_data.username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 验证密码
        if not crud.verify_password(form_data.password, user.hashed_pwd):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 生成访问令牌
        access_token = auth_service.create_access_token(
            user.id, user.user_name, user.is_super
        )

        return UserLoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 3600,  # 24小时
            user={
                "id": user.id,
                "user_name": user.user_name,
                "is_active": user.is_active,
                "is_super": user.is_super,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录服务异常"
        )


@user_router.post("/create", response_model=Dict[str, Any])
async def register(
        user_data: UserCenterCreate,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """用户注册"""
    try:
        crud = UserCenterCRUD(db)
        exist = crud.get_user_by_username(user_data.user_name)
        if exist:
            return {
                "status": 1,
                "msg": "用户名已存在"
            }

        user = crud.create_user(user_data)

        return {
            "status": 0,
            "msg": '创建成功',
            "data": {
                "id": user.id,
                "user_name": user.user_name,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat()
            }
        }
    except HTTPException as e:
        logger.error(f"创建用户失败: {e}")
        raise HTTPException(status_code=500, detail="创建用户失败")


@user_router.post("/logout")
async def logout(
        current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """用户登出"""
    return {"message": "登出成功"}


@user_router.post("/toggle-status/{user_id}", response_model=Dict[str, Any])
async def toggle_user_status(
        user_id: int,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """切换用户状态（激活/禁用）"""
    try:
        crud = UserCenterCRUD(db)
        success, message, user = crud.toggle_user_status(user_id)

        if not success:
            return {
                "status": 1,
                "msg": message
            }

        return {
            "status": 0,
            "msg": message,
            "data": {
                "id": user.id,
                "is_active": user.is_active
            }
        }

    except Exception as e:
        logger.error(f"切换用户状态失败: {e}")
        raise HTTPException(status_code=500, detail="状态切换失败")


@user_router.post("/reset-password/{user_id}", response_model=Dict[str, Any])
async def reset_user_password(
        user_id: int,
        new_password: str,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """重置用户密码"""
    try:
        if len(new_password) < 6:
            return {
                "status": 1,
                "msg": "密码长度至少6位"
            }
        crud = UserCenterCRUD(db)
        success, message = crud.reset_user_password(user_id, new_password)

        return {
            "status": 0 if success else 1,
            "msg": message
        }

    except Exception as e:
        logger.error(f"重置密码失败: {e}")
        raise HTTPException(status_code=500, detail="重置密码失败")
