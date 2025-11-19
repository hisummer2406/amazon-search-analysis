from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class AnalysisSearchRequest(BaseModel):
    """分析搜索请求模型"""
    # 分页参数
    page: int = Field(default=1, ge=1, description="页码")
    perPage: int = Field(default=50, ge=1, le=1501, description="每页数量")

    # 搜索条件
    orderBy: Optional[str] = Field(None, description="排序字段")
    orderDir: Optional[str] = Field(None, description="排序规则")

    # 基础搜索条件
    keyword: Optional[str] = Field(None, description="关键词搜索")
    brand: Optional[str] = Field(None, description="品牌搜索")
    category: Optional[str] = Field(None, description="类目搜索")
    asin: Optional[str] = Field(None, description="ASIN搜索")
    product_title: Optional[str] = Field(None, description="商品标题搜索")
    report_date: Optional[str] = Field(None, description="报告日期筛选")

    # 高级搜索 - 排名范围
    daily_ranking_min: Optional[int] = Field(None, description="日排名最小值")
    daily_ranking_max: Optional[int] = Field(None, description="日排名最大值")
    weekly_ranking_min: Optional[int] = Field(None, description="周排名最小值")
    weekly_ranking_max: Optional[int] = Field(None, description="周排名最大值")

    # 高级搜索 - 变化范围
    daily_change_min: Optional[int] = Field(None, description="日变化最小值")
    daily_change_max: Optional[int] = Field(None, description="日变化最大值")
    weekly_change_min: Optional[int] = Field(None, description="周变化最小值")
    weekly_change_max: Optional[int] = Field(None, description="周变化最大值")

    # 高级搜索 - 份额和转化率范围
    click_share_min: Optional[float] = Field(None, description="点击份额最小值")
    click_share_max: Optional[float] = Field(None, description="点击份额最大值")
    conversion_share_min: Optional[float] = Field(None, description="转化份额最小值")
    conversion_share_max: Optional[float] = Field(None, description="转化份额最大值")
    conversion_rate_min: Optional[float] = Field(None, description="转化率最小值")
    conversion_rate_max: Optional[float] = Field(None, description="转化率最大值")

    # 高级搜索 - 布尔值筛选
    is_new_day: Optional[bool] = Field(None, description="是否日新品")
    is_new_week: Optional[bool] = Field(None, description="是否周新品")


class AnalysisDataItem(BaseModel):
    """分析数据项模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword: str

    # 排名数据
    current_rangking_day: int
    previous_rangking_day: int
    ranking_change_day: int
    current_rangking_week: int
    previous_rangking_week: int
    ranking_change_week: int

    # 趋势图数据
    ranking_trend_day: List[Any] = Field(default_factory=list)

    # 商品信息
    top_brand: str
    top_category: str
    top_product_asin: str
    top_product_title: str

    # 数据指标
    top_product_click_share: float
    top_product_conversion_share: float
    conversion_rate: float

    # 状态标识
    is_new_day: bool
    is_new_week: bool

    # 日期信息
    report_date_day: Optional[str] = None
    report_date_week: Optional[str] = None
    created_at: Optional[str] = None


class AnalysisSearchResponse(BaseModel):
    """分析搜索响应模型"""
    status: int = 0
    msg: str = "查询成功"
    data: Dict[str, Any]


class PaginationData(BaseModel):
    """分页数据模型"""
    items: List[AnalysisDataItem]
    count: int
    page: int
    perPage: int
