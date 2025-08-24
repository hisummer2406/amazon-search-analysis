# app/middleware/auth_middleware.py
"""简化认证中间件 - 修复登录页面路由问题"""
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
            "/admin/user",
            "/admin/analysis",
            "/api/analysis/search",
            "/api/user/list",
            "/api/user/register",
        ]

        # 排除的路径 - 不需要认证
        self.exclude_paths = [
            "/admin/login",  # 登录页面
            "/api/auth/login",  # 登录API
            "/api/auth/profile",  # 用户信息API
            "/static/",  # 静态文件
            "/docs",  # API文档
            "/redoc",  # API文档
            "/health",  # 健康检查
        ]

    async def dispatch(self, request: Request, call_next):
        """中间件主逻辑"""
        path = request.url.path

        # 检查是否需要认证
        if not self._needs_auth(path):
            return await call_next(request)

        # 对于需要认证的路径，检查登录状态
        try:
            # 首先检查是否有Authorization头
            auth_header = request.headers.get('Authorization')

            print(f"🔥Authorization: {auth_header}")

            # 如果是浏览器访问且没有token，重定向到登录页
            if not auth_header or not auth_header.startswith('Bearer '):
                # 检查是否是API请求
                if path.startswith('/api/'):
                    # API请求返回401错误
                    from fastapi import HTTPException, status
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="未授权访问"
                    )
                else:
                    print(f"??path: {path}")
                    # 浏览器请求重定向到登录页
                    return RedirectResponse(url="/admin/login", status_code=302)

            # 验证token
            from database import SessionFactory
            from app.services.login_auth import auth_service
            from app.crud.user_crud import UserCenterCRUD

            token = auth_header.split(' ')[1]
            payload = auth_service.decode_access_token(token)
            if not payload:
                if path.startswith('/api/'):
                    from fastapi import HTTPException, status
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token无效或已过期"
                    )
                else:
                    return RedirectResponse(url="/admin/login", status_code=302)

            # 验证用户
            with SessionFactory() as db:
                crud = UserCenterCRUD(db)
                user = crud.get_user_by_username(payload.get('username'))

                if not user or not user.is_active:
                    if path.startswith('/api/'):
                        from fastapi import HTTPException, status
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="用户不存在或已禁用"
                        )
                    else:
                        return RedirectResponse(url="/admin/login", status_code=302)

                # 用户管理需要超级用户权限
                if path.startswith('/admin/user') and not user.is_super:
                    if path.startswith('/api/'):
                        from fastapi import HTTPException, status
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="需要超级管理员权限"
                        )
                    else:
                        return RedirectResponse(url="/admin/", status_code=302)

                # 将用户信息注入请求
                request.state.current_user = user

        except Exception as e:
            logger.error(f"认证中间件异常: {e}")
            if path.startswith('/api/'):
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="认证服务异常"
                )
            else:
                return RedirectResponse(url="/admin/login", status_code=302)

        return await call_next(request)

    def _needs_auth(self, path: str) -> bool:
        """判断路径是否需要认证"""
        # 首先检查排除路径
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False

        # 检查需要认证的路径
        for protected_path in self.protected_paths:
            if path.startswith(protected_path):
                return True

        # 默认不需要认证
        return False

    def _needs_auth2(self, path: str) -> bool:
        """判断路径是否需要认证"""
        print(f"🔍 Checking path: {path}")  # 更详细的日志
        # 首先检查排除路径
        excluded = False
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                print(f"🚫 Path {path} starts with excluded path: {exclude_path}")
                excluded = True
                return False
        if excluded:
            print(f"✅ Path {path} is excluded.")
        else:
            print(f"ℹ️ Path {path} is not in excluded paths.")

        # 检查需要认证的路径
        protected = False
        for protected_path in self.protected_paths:
            if path.startswith(protected_path):
                print(f"🔒 Path {path} starts with protected path: {protected_path}")
                protected = True
                return True
        if protected:
            print(f"✅ Path {path} is protected.")
        else:
            print(f"ℹ️ Path {path} is not in protected paths.")

        # 默认不需要认证
        print(f"⚠️ Path {path} does not need authentication.")
        return False