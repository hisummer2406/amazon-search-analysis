from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from passlib.context import CryptContext
from app.models.user_models import UserCenter
from app.schemas.user_schemas import UserCenterCreate, UserCenterUpdate, UserCenterList

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCenterCRUD:
    """用户中心CRUD操作 - 包含业务逻辑"""

    def __init__(self, db: Session):
        self.db = db

    def get_users_paginated(
            self,
            page: int = 1,
            per_page: int = 20,
            user_name: Optional[str] = None,
            is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """分页获取用户列表"""
        try:
            # 计算偏移量
            skip = (page - 1) * per_page

            # 获取用户列表
            users = self.get_users_list(
                skip=skip,
                limit=per_page,
                user_name=user_name,
                is_active=is_active
            )

            # 获取总数
            total = self.count_users(
                search=user_name,
                is_active=is_active
            )

            # 转换为响应模型
            user_list = [UserCenterList.model_validate(user) for user in users]

            return {
                "items": user_list,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }

        except Exception as e:
            logger.error(f"分页获取用户列表失败: {e}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "pages": 0
            }

    def get_user_by_id(self, user_id: int) -> Optional[UserCenter]:
        """根据ID获取用户"""
        try:
            return self.db.query(UserCenter).filter(UserCenter.id == user_id).first()
        except Exception as e:
            logger.error(f"根据ID获取用户失败: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[UserCenter]:
        """根据用户名获取用户"""
        try:
            return self.db.query(UserCenter).filter(UserCenter.user_name == username).first()
        except Exception as e:
            logger.error(f"根据用户名获取用户失败: {e}")
            return None

    def get_users_list(
            self,
            skip: int = 0,
            limit: int = 100,
            user_name: Optional[str] = None,
            is_active: Optional[bool] = None
    ) -> List[UserCenter]:
        """获取用户列表"""
        try:
            query = self.db.query(UserCenter)

            # 搜索条件
            if user_name:
                query = query.filter(UserCenter.user_name.ilike(f"%{user_name}%"))

            # 状态筛选
            if is_active is not None:
                query = query.filter(UserCenter.is_active == is_active)

            # 排序和分页
            return query.order_by(desc(UserCenter.created_at)).offset(skip).limit(limit).all()

        except Exception as e:
            logger.error(f"获取用户列表失败: {e}")
            return []

    def count_users(
            self,
            search: Optional[str] = None,
            is_active: Optional[bool] = None
    ) -> int:
        """统计用户总数"""
        try:
            query = self.db.query(func.count(UserCenter.id))

            # 搜索条件
            if search:
                query = query.filter(UserCenter.user_name.ilike(f"%{search}%"))

            # 状态筛选
            if is_active is not None:
                query = query.filter(UserCenter.is_active == is_active)

            return query.scalar() or 0

        except Exception as e:
            logger.error(f"统计用户总数失败: {e}")
            return 0

    def create_user(self, user_data: UserCenterCreate) -> Tuple[bool, str, Optional[UserCenter]]:
        """创建用户 - 包含业务逻辑验证"""
        try:
            # 检查用户名是否已存在
            existing_user = self.get_user_by_username(user_data.user_name)
            if existing_user:
                logger.warning(f"用户名 {user_data.user_name} 已存在")
                return False, "用户名已存在", None

            # 创建用户对象
            hashed_password = self.hash_password(user_data.password)
            db_user = UserCenter(
                user_name=user_data.user_name,
                hashed_pwd=hashed_password,
                is_active=user_data.is_active,
                is_super=user_data.is_super
            )

            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)

            logger.info(f"用户创建成功: {db_user.id} - {db_user.user_name}")
            return True, "用户创建成功", db_user

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建用户失败: {e}")
            return False, f"创建用户失败: {str(e)}", None

    def update_user(
            self,
            user_id: int,
            user_data: UserCenterUpdate
    ) -> Tuple[bool, str, Optional[UserCenter]]:
        """更新用户 - 包含业务逻辑验证"""
        try:
            # 检查用户是否存在
            db_user = self.get_user_by_id(user_id)
            if not db_user:
                return False, "用户不存在", None

            # 如果更新用户名，检查是否与其他用户冲突
            if user_data.user_name and user_data.user_name != db_user.user_name:
                name_conflict = self.get_user_by_username(user_data.user_name)
                if name_conflict:
                    return False, "用户名已被其他用户使用", None

            # 更新字段
            update_data = user_data.dict(exclude_unset=True)

            # 如果包含密码，需要加密
            if 'password' in update_data:
                update_data['hashed_pwd'] = self.hash_password(update_data.pop('password'))

            for key, value in update_data.items():
                if hasattr(db_user, key):
                    setattr(db_user, key, value)

            # 手动更新时间
            db_user.updated_at = datetime.now()

            self.db.commit()
            self.db.refresh(db_user)

            logger.info(f"用户更新成功: {user_id}")
            return True, "用户更新成功", db_user

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新用户失败: {e}")
            return False, f"更新用户失败: {str(e)}", None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False

    def hash_password(self, password: str) -> str:
        """加密密码"""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"密码加密失败: {e}")
            raise

    def authenticate_user(self, username: str, password: str) -> Optional[UserCenter]:
        """用户认证"""
        try:
            user = self.get_user_by_username(username)
            if not user:
                return None

            if not user.is_active:
                return None

            if not self.verify_password(password, user.hashed_pwd):
                return None

            return user

        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return None

    def toggle_user_status(self, user_id: int) -> Tuple[bool, str, Optional[UserCenter]]:
        """切换用户状态（激活/禁用）- 包含业务逻辑验证"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False, "用户不存在", None

            # 不能禁用超级管理员
            if user.is_super and user.is_active:
                return False, "不能禁用超级管理员", None

            # 切换状态
            update_data = UserCenterUpdate(is_active=not user.is_active)
            success, message, updated_user = self.update_user(user_id, update_data)

            if not success:
                return False, "状态切换失败", None

            status_text = "激活" if updated_user.is_active else "禁用"
            logger.info(f"用户状态切换成功: {user_id} -> {status_text}")
            return True, f"用户已{status_text}", updated_user

        except Exception as e:
            logger.error(f"切换用户状态失败: {e}")
            return False, f"状态切换失败: {str(e)}", None

    def reset_user_password(self, user_id: int, new_password: str) -> Tuple[bool, str]:
        """重置用户密码"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False, "用户不存在"

            # 更新密码
            update_data = UserCenterUpdate(password=new_password)
            success, message, updated_user = self.update_user(user_id, update_data)

            if not success:
                return False, "密码重置失败"

            logger.info(f"用户密码重置成功: {user_id}")
            return True, "密码重置成功"

        except Exception as e:
            logger.error(f"重置用户密码失败: {e}")
            return False, f"密码重置失败: {str(e)}"
