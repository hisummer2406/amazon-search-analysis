import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from config import settings


class AuthService:
    """认证服务"""

    @staticmethod
    def create_access_token(user_id: int, username: str, is_super: bool) -> str:
        """生成访问令牌"""
        payload = {
            "user_id": user_id,
            "username": username,
            "is_super": is_super,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, settings.ADMIN_SECRET_KEY, algorithm="HS256")

    @staticmethod
    def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
        """解码访问令牌"""
        try:
            payload = jwt.decode(token, settings.ADMIN_SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None


# 创建认证服务实例
auth_service = AuthService()
