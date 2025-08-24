import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from app.crud.user_crud import UserCenterCRUD
from app.schemas.user_schemas import (UserCenterCreate, UserCenterUpdate)

logger = logging.getLogger(__name__)

user_router = APIRouter()


@user_router.get("/list", response_model=Dict[str, Any])
async def get_users_list(
        page: int = Query(1, ge=1, description="页码"),
        per_page: int = Query(20, ge=1, le=100, description="每页数量"),
        user_name: Optional[str] = Query(None, description="搜索关键词"),
        is_active: Optional[bool] = Query(default=True, description="用户状态筛选"),
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


@user_router.get("/detail/{user_id}", response_model=Dict[str, Any])
async def get_user_detail(
        user_id: int,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取用户详情"""
    try:
        crud = UserCenterCRUD(db)
        user = crud.get_user_by_id(user_id)

        if not user:
            return {
                "status": 1,
                "msg": "用户不存在"
            }

        return {
            "status": 0,
            "msg": "获取成功",
            "data": {
                "id": user.id,
                "user_name": user.user_name,
                "is_active": user.is_active,
                "is_super": user.is_super,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
        }

    except Exception as e:
        logger.error(f"获取用户详情失败: {e}")
        return {
            "status": 1,
            "msg": "获取用户详情失败"
        }


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

        success, message, user = crud.create_user(user_data)

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
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        raise HTTPException(status_code=500, detail="创建用户失败")


@user_router.put("/update/{user_id}", response_model=Dict[str, Any])
async def update_user(
        user_id: int,
        user_data: UserCenterUpdate,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """更新用户信息"""
    try:
        crud = UserCenterCRUD(db)
        success, message, user = crud.update_user(user_id, user_data)

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
                "user_name": user.user_name,
                "is_active": user.is_active,
                "is_super": user.is_super,
                "updated_at": user.updated_at.isoformat()
            }
        }

    except Exception as e:
        logger.error(f"更新用户失败: {e}")
        return {
            "status": 1,
            "msg": "更新用户失败"
        }


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
