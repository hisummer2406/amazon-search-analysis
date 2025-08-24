# app/middleware/auth_middleware.py
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, JSONResponse

logger = logging.getLogger(__name__)


class AdminAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.protected_paths = [
            "/api/analysis/",
            "/api/user/",
            "/api/upload/"
        ]
        self.exclude_paths = [
            "/admin/login",
            "/api/auth/login",
            "/api/auth/profile",
            "/static",
            "/docs",
            "/redoc",
            "/health",
            "/"
        ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        logger.debug(f"处理请求路径: {path}")

        if not self._needs_auth(path):
            logger.debug(f"路径 {path} 无需认证")
            return await call_next(request)

        auth_header = request.headers.get('Authorization')
        logger.debug(f"认证头: {auth_header}")

        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning(f"路径 {path} 缺少认证头")
            return self._handle_unauthorized(path)

        try:
            from database import SessionFactory
            from app.services.login_auth import auth_service
            from app.crud.user_crud import UserCenterCRUD

            token = auth_header.split(' ')[1]
            payload = auth_service.decode_access_token(token)

            if not payload:
                logger.warning(f"路径 {path} token无效")
                return self._handle_unauthorized(path)

            with SessionFactory() as db:
                crud = UserCenterCRUD(db)
                user = crud.get_user_by_username(payload.get('username'))

                if not user or not user.is_active:
                    logger.warning(f"路径 {path} 用户不存在或未激活")
                    return self._handle_unauthorized(path)

                request.state.current_user = user
                logger.debug(f"用户 {user.user_name} 认证成功")

        except Exception as e:
            logger.error(f"认证异常: {e}")
            return self._handle_unauthorized(path)

        return await call_next(request)

    def _needs_auth(self, path: str) -> bool:
        """判断路径是否需要认证"""
        # /admin 后台页面不需要认证（由amis自己处理）
        if path.startswith('/admin'):
            return False

        # 先检查排除路径
        for exclude in self.exclude_paths:
            if path.startswith(exclude):
                return False

        # 再检查保护路径
        for protected in self.protected_paths:
            if path.startswith(protected):
                return True

        return False

    def _handle_unauthorized(self, path: str):
        if path.startswith('/api/'):
            return JSONResponse(
                status_code=401,
                content={"status": 1, "msg": "未授权访问", "data": None}
            )
        else:
            return RedirectResponse(url="/admin/login", status_code=302)