# app/auth/simple_auth.py
"""简化版认证模块 - 只提供后台登录验证和超级用户管理"""
import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db, SessionFactory
from app.user.user_crud import UserCenterCRUD
from app.user.user_model import UserCenter
from app.auth.login_auth import auth_service

logger = logging.getLogger(__name__)
security = HTTPBearer()


class SimpleAuth:
    """简化认证类"""

    @staticmethod
    async def login(username: str, password: str) -> dict:
        """用户登录"""
        with SessionFactory() as db:
            crud = UserCenterCRUD(db)
            user = crud.authenticate_user(username, password)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误"
                )

            token = auth_service.create_access_token(user.id, user.user_name, user.is_super)

            return {
                'access_token': token,
                'token_type': 'bearer',
                'expires_in': 24 * 3600 * 3,
                'user': {
                    'id': user.id,
                    'username': user.user_name,
                    'is_super': user.is_super
                }
            }

    @staticmethod
    def get_current_user(
            credentials: HTTPAuthorizationCredentials = Depends(security),
            db: Session = Depends(get_db)
    ) -> UserCenter:
        """获取当前用户"""
        payload = auth_service.decode_access_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效令牌"
            )

        crud = UserCenterCRUD(db)
        user = crud.get_user_by_username(payload["username"])
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已禁用"
            )

        return user

    @staticmethod
    def get_super_user():
        """获取超级用户依赖"""

        def _get_super_user(current_user: UserCenter = Depends(simple_auth.get_current_user)) -> UserCenter:
            if not current_user.is_super:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="需要超级管理员权限"
                )
            return current_user

        return _get_super_user


# 全局认证实例
simple_auth = SimpleAuth()