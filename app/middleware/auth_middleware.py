# app/middleware/auth_middleware.py
"""简化认证中间件 - 自动重定向到登录页面"""
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

logger = logging.getLogger(__name__)


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """后台认证中间件"""

    def __init__(self, app):
        super().__init__(app)
        # 需要认证的路径
        self.protected_paths = [
            "/admin/user",  # 用户管理页面
            "/api/user/",  # 用户API
        ]

        # 排除的路径
        self.exclude_paths = [
            "/admin/login",
            "/api/auth/login",
            "/static/",
            "/docs",
            "/redoc"
        ]

    async def dispatch(self, request: Request, call_next):
        """中间件主逻辑"""
        path = request.url.path

        # 检查是否需要认证
        if not self._needs_auth(path):
            return await call_next(request)

        # 尝试获取用户
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return RedirectResponse(url="/admin/login", status_code=302)

            from database import SessionFactory
            from app.services.login_auth import auth_service
            from app.crud.user_crud import UserCenterCRUD

            token = auth_header.split(' ')[1]
            payload = auth_service.decode_access_token(token)
            if not payload:
                return RedirectResponse(url="/admin/login", status_code=302)

            with SessionFactory() as db:
                crud = UserCenterCRUD(db)
                user = crud.get_user_by_username(payload.get('username'))

                if not user or not user.is_active:
                    return RedirectResponse(url="/admin/login", status_code=302)

                # 用户管理需要超级用户权限
                if path.startswith('/admin/user') and not user.is_super:
                    return RedirectResponse(url="/admin/login", status_code=302)

                # 将用户信息注入请求
                request.state.current_user = user

        except Exception as e:
            logger.error(f"认证中间件异常: {e}")
            return RedirectResponse(url="/admin/login", status_code=302)

        return await call_next(request)

    def _needs_auth(self, path: str) -> bool:
        """判断路径是否需要认证"""
        # 检查排除路径
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False

        # 检查需要认证的路径
        for protected_path in self.protected_paths:
            if path.startswith(protected_path):
                return True

        return False