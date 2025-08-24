import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from database import get_db
from app.services.analysis_service import AnalysisService
from app.schemas.analysis_schemas import AnalysisSearchRequest, AnalysisSearchResponse
from app.services.simple_auth import simple_auth

logger = logging.getLogger(__name__)

current_user = Depends(simple_auth.get_current_user)

analysis_router = APIRouter()


def _parse_optional_value(value: Optional[str], value_type: type = str):
    """解析可选参数，处理空字符串和类型转换"""
    if not value or value.strip() == "":
        return None

    try:
        if value_type == int:
            return int(value)
        elif value_type == float:
            return float(value)
        elif value_type == bool:
            return value.lower() in ["true", "1", "yes", "是"]
        else:
            return value.strip()
    except (ValueError, TypeError):
        return None


@analysis_router.get("/search", response_model=AnalysisSearchResponse)
async def search_data(
        current_user: dict = Depends(simple_auth.get_current_user),  # 添加这行
        # 分页参数
        page: int = Query(1, ge=1, description="页码"),
        perPage: int = Query(50, ge=1, le=200, description="每页数量"),

        # 基础搜索条件参数
        keyword: Optional[str] = Query(None, description="关键词搜索"),
        brand: Optional[str] = Query(None, description="品牌搜索"),
        category: Optional[str] = Query(None, description="类目搜索"),
        asin: Optional[str] = Query(None, description="ASIN搜索"),
        product_title: Optional[str] = Query(None, description="商品标题搜索"),
        report_date: Optional[str] = Query(None, description="报告日期筛选"),

        # 高级搜索 - 排名范围参数
        daily_ranking_min: Optional[str] = Query(None, description="日排名最小值"),
        daily_ranking_max: Optional[str] = Query(None, description="日排名最大值"),
        weekly_ranking_min: Optional[str] = Query(None, description="周排名最小值"),
        weekly_ranking_max: Optional[str] = Query(None, description="周排名最大值"),

        # 高级搜索 - 变化范围参数
        daily_change_min: Optional[str] = Query(None, description="日变化最小值"),
        daily_change_max: Optional[str] = Query(None, description="日变化最大值"),
        weekly_change_min: Optional[str] = Query(None, description="周变化最小值"),
        weekly_change_max: Optional[str] = Query(None, description="周变化最大值"),

        # 高级搜索 - 份额和转化率范围参数
        click_share_min: Optional[str] = Query(None, description="点击份额最小值"),
        click_share_max: Optional[str] = Query(None, description="点击份额最大值"),
        conversion_share_min: Optional[str] = Query(None, description="转化份额最小值"),
        conversion_share_max: Optional[str] = Query(None, description="转化份额最大值"),
        conversion_rate_min: Optional[str] = Query(None, description="转化率最小值"),
        conversion_rate_max: Optional[str] = Query(None, description="转化率最大值"),

        # 高级搜索 - 布尔值参数
        is_new_day: Optional[str] = Query(None, description="是否日新品"),
        is_new_week: Optional[str] = Query(None, description="是否周新品"),

        # 依赖注入
        db: Session = Depends(get_db),
        # current_user: dict = Depends(get_current_user)  # 暂时注释掉用户验证
) -> Dict[str, Any]:
    """搜索亚马逊数据 - 重构后的简洁版本"""
    try:
        # 构建搜索请求参数
        search_params = AnalysisSearchRequest(
            # 分页参数
            page=page,
            perPage=perPage,

            # 基础搜索条件
            keyword=_parse_optional_value(keyword),
            brand=_parse_optional_value(brand),
            category=_parse_optional_value(category),
            asin=_parse_optional_value(asin),
            product_title=_parse_optional_value(product_title),
            report_date=_parse_optional_value(report_date),

            # 排名范围参数
            daily_ranking_min=_parse_optional_value(daily_ranking_min, int),
            daily_ranking_max=_parse_optional_value(daily_ranking_max, int),
            weekly_ranking_min=_parse_optional_value(weekly_ranking_min, int),
            weekly_ranking_max=_parse_optional_value(weekly_ranking_max, int),

            # 变化范围参数
            daily_change_min=_parse_optional_value(daily_change_min, int),
            daily_change_max=_parse_optional_value(daily_change_max, int),
            weekly_change_min=_parse_optional_value(weekly_change_min, int),
            weekly_change_max=_parse_optional_value(weekly_change_max, int),

            # 份额和转化率范围参数
            click_share_min=_parse_optional_value(click_share_min, float),
            click_share_max=_parse_optional_value(click_share_max, float),
            conversion_share_min=_parse_optional_value(conversion_share_min, float),
            conversion_share_max=_parse_optional_value(conversion_share_max, float),
            conversion_rate_min=_parse_optional_value(conversion_rate_min, float),
            conversion_rate_max=_parse_optional_value(conversion_rate_max, float),

            # 布尔值参数
            is_new_day=_parse_optional_value(is_new_day, bool),
            is_new_week=_parse_optional_value(is_new_week, bool)
        )

        # 调用服务层处理业务逻辑
        analysis_service = AnalysisService(db)
        result = analysis_service.search_data(search_params)

        return result.model_dump()

    except Exception as e:
        logger.error(f"搜索数据API失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )
