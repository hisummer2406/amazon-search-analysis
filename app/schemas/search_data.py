from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date
from decimal import Decimal


class SearchDataBase(BaseModel):
    keyword: str = Field(..., max_length=500, description="搜索关键词")

    # 日数据字段
    current_rangking_day: int = Field(..., description="当前搜索频率排名 日")
    report_date_day: date = Field(..., description="报告日期 天")
    previous_rangking_day: int = Field(..., description="上期排名 天")
    ranking_change_day: int = Field(default=0, description="排名变化 日")
    ranking_trend_day: List[Dict[str, Any]] = Field(default_factory=list, description="排名趋势 日")

    # 周数据字段
    current_rangking_week: int = Field(..., description="当前搜索频率排名 周")
    report_date_week: date = Field(..., description="报告日期 周")
    previous_rangking_week: int = Field(..., description="上期排名 周")
    ranking_change_week: int = Field(default=0, description="排名变化 周")

    # 商品信息
    top_brand: Optional[str] = Field(None, max_length=255, description="顶级品牌")
    top_category: Optional[str] = Field(None, max_length=255, description="顶级类别")
    top_product_asin: Optional[str] = Field(None, max_length=255, description="顶级商品ASIN")
    top_product_title: Optional[str] = Field(None, max_length=500, description="顶级商品标题")
    top_product_click_share: Decimal = Field(default=0, description="顶级商品点击份额")
    top_product_conversion_share: Decimal = Field(default=0, description="顶级商品转化份额")

    # 标记字段
    is_new_day: Optional[bool] = Field(None, description="是否为新的日数据")
    is_new_week: Optional[bool] = Field(None, description="是否为新的周数据")


class SearchDataCreate(SearchDataBase):
    pass


class SearchDataUpdate(BaseModel):
    """用于部分更新的模型"""
    # 日数据更新
    current_rangking_day: Optional[int] = None
    report_date_day: Optional[date] = None
    previous_rangking_day: Optional[int] = None
    ranking_change_day: Optional[int] = None
    ranking_trend_day: Optional[List[Dict[str, Any]]] = None
    is_new_day: Optional[bool] = None

    # 周数据更新
    current_rangking_week: Optional[int] = None
    report_date_week: Optional[date] = None
    previous_rangking_week: Optional[int] = None
    ranking_change_week: Optional[int] = None
    is_new_week: Optional[bool] = None

    # 商品信息更新
    top_brand: Optional[str] = None
    top_category: Optional[str] = None
    top_product_title: Optional[str] = None
    top_product_click_share: Optional[Decimal] = None
    top_product_conversion_share: Optional[Decimal] = None


class SearchData(SearchDataBase):
    id: int
    created_at: date

    class Config:
        from_attributes = True


class SearchDataSummary(BaseModel):
    """搜索数据摘要"""
    keyword: str
    top_product_asin: str
    top_product_title: str
    latest_day_ranking: int
    latest_week_ranking: int
    click_share: Decimal
    conversion_share: Decimal
    day_trend: str  # 'up', 'down', 'stable'
    week_trend: str