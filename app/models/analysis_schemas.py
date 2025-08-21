from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, Integer, String, Date, Boolean, Text, DateTime, Numeric, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date
from typing import Optional
import enum

from database import Base


class StatusEnum(enum.Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AmazonOriginSearchData(Base):
    __tablename__ = "amazon_origin_search_data"
    __table_args__ = {"schema": "analysis"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    keyword: Mapped[str] = mapped_column(String(500), nullable=False, default='')

    # 日排名字段
    current_rangking_day: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    report_date_day: Mapped[date] = mapped_column(Date, nullable=False)
    previous_rangking_day: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ranking_change_day: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ranking_trend_day: Mapped[dict] = mapped_column(JSONB, nullable=False, default=lambda: [])

    # 周排名字段
    current_rangking_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    report_date_week: Mapped[date] = mapped_column(Date, nullable=False)
    previous_rangking_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ranking_change_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Top产品信息
    top_brand: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    top_category: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    top_product_asin: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    top_product_title: Mapped[str] = mapped_column(String(500), nullable=False, default='')
    top_product_click_share: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    top_product_conversion_share: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # 第二名产品信息
    brand_2nd: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    category_2nd: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    product_asin_2nd: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    product_title_2nd: Mapped[str] = mapped_column(String(500), nullable=False, default='')
    product_click_share_2nd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    product_conversion_share_2nd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # 第三名产品信息
    brand_3rd: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    category_3rd: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    product_asin_3rd: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    product_title_3rd: Mapped[str] = mapped_column(String(500), nullable=False, default='')
    product_click_share_3rd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    product_conversion_share_3rd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # 状态标识
    is_new_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_new_week: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(),
                                                 onupdate=func.now())
