from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from app.services.login_auth import auth_service
from app.crud.user_crud import UserCenterCRUD

security = HTTPBearer()


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> dict:
    """获取当前用户依赖"""
    token = credentials.credentials

    # 解码令牌
    payload = auth_service.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证用户是否存在且活跃
    curd = UserCenterCRUD(db)
    user = curd.get_user_by_username(payload["user_name"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": user.id,
        "user_name": user.user_name,
        "is_super": user.is_super,
        "user_obj": user
    }


def get_current_super_user(
        current_user: dict = Depends(get_current_user)
) -> dict:
    """获取当前超级用户依赖"""
    if not current_user.get("is_super", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user
