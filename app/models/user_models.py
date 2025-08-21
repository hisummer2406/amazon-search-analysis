from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, Integer, String, func
from datetime import datetime

from database import Base

class UserCenter(Base):
    __tablename__ = "user_center"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_pwd: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_super: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())
