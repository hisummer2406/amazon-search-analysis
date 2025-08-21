from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class UserCenterBase(BaseModel):
    """用户登录模型"""
    user_name: str = Field(..., min_length=3, max_length=50, description="用户名")
    is_active: bool = Field(default=True, description="账号是否可用")
    is_super: bool = Field(default=False, description="是否为超级用户")


class UserCenterCreate(UserCenterBase):
    """用户注册模型"""
    password: str = Field(..., min_length=6, max_length=128, description="密码")

    @field_validator('user_name')
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        return v


class UserCenterUpdate(BaseModel):
    user_name: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    password: Optional[str] = Field(None, min_length=6, max_length=50, description="密码")
    is_active: Optional[bool] = Field(None, description="是否激活")

    @field_validator('user_name')
    @classmethod
    def validate_username(cls, v):
        if v and not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v.lower() if v else v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v and len(v) < 6:
            raise ValueError('密码长度至少6位')
        return v


class UserCenter(UserCenterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class UserCenterList(BaseModel):
    """用户列表响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_name: str
    is_active: bool
    is_super: bool
    created_at: datetime
    updated_at: datetime


class UserCenterLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserCenterLoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    user_info: UserCenter


class UserLoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间(秒)")
    user: dict = Field(..., description="用户信息")
