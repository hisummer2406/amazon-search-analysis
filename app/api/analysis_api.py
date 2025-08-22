import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func, asc
from datetime import datetime, date

from database import get_db
from app.models.analysis_schemas import AmazonOriginSearchData
from app.dependencies.login_auth import get_current_user

logger = logging.getLogger(__name__)

analysis_router = APIRouter()


def _parse_optional_int(value: str) -> Optional[int]:
    """解析可选整数参数，处理空字符串"""
    if not value or value.strip() == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_optional_float(value: str) -> Optional[float]:
    """解析可选浮点数参数，处理空字符串"""
    if not value or value.strip() == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_optional_bool(value: str) -> Optional[bool]:
    """解析可选布尔值参数，处理空字符串"""
    if not value or value.strip() == "":
        return None
    if value.lower() in ["true", "1", "yes", "是"]:
        return True
    elif value.lower() in ["false", "0", "no", "否"]:
        return False
    return None


@analysis_router.get("/search")
async def search_data(
        # 分页参数
        page: int = Query(1, ge=1, description="页码"),
        perPage: int = Query(50, ge=1, le=200, description="每页数量"),

        # 基础搜索条件参数 - 使用字符串类型避免类型转换错误
        keyword: Optional[str] = Query(None, description="关键词搜索"),
        brand: Optional[str] = Query(None, description="品牌搜索"),
        category: Optional[str] = Query(None, description="类目搜索"),
        asin: Optional[str] = Query(None, description="ASIN搜索"),
        product_title: Optional[str] = Query(None, description="商品标题搜索"),
        report_date: Optional[str] = Query(None, description="报告日期筛选"),

        # 高级搜索 - 排名范围参数（使用字符串避免转换错误）
        daily_ranking_min: Optional[str] = Query(None, description="日排名最小值"),
        daily_ranking_max: Optional[str] = Query(None, description="日排名最大值"),
        weekly_ranking_min: Optional[str] = Query(None, description="周排名最小值"),
        weekly_ranking_max: Optional[str] = Query(None, description="周排名最大值"),

        # 高级搜索 - 变化范围参数（使用字符串避免转换错误）
        daily_change_min: Optional[str] = Query(None, description="日变化最小值"),
        daily_change_max: Optional[str] = Query(None, description="日变化最大值"),
        weekly_change_min: Optional[str] = Query(None, description="周变化最小值"),
        weekly_change_max: Optional[str] = Query(None, description="周变化最大值"),

        # 高级搜索 - 份额和转化率范围参数（使用字符串避免转换错误）
        click_share_min: Optional[str] = Query(None, description="点击份额最小值"),
        click_share_max: Optional[str] = Query(None, description="点击份额最大值"),
        conversion_share_min: Optional[str] = Query(None, description="转化份额最小值"),
        conversion_share_max: Optional[str] = Query(None, description="转化份额最大值"),
        conversion_rate_min: Optional[str] = Query(None, description="转化率最小值"),
        conversion_rate_max: Optional[str] = Query(None, description="转化率最大值"),

        # 高级搜索 - 布尔值参数（使用字符串避免转换错误）
        is_new_day: Optional[str] = Query(None, description="是否日新品"),
        is_new_week: Optional[str] = Query(None, description="是否周新品"),

        # 依赖注入
        db: Session = Depends(get_db),
        # current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """搜索亚马逊数据"""
    try:
        # 计算偏移量
        skip = (page - 1) * perPage

        # 构建查询
        query = db.query(AmazonOriginSearchData)

        # 解析参数并应用筛选条件
        query = _apply_search_filters(
            query=query,
            keyword=keyword,
            brand=brand,
            category=category,
            asin=asin,
            product_title=product_title,
            report_date=report_date,
            daily_ranking_min=_parse_optional_int(daily_ranking_min),
            daily_ranking_max=_parse_optional_int(daily_ranking_max),
            weekly_ranking_min=_parse_optional_int(weekly_ranking_min),
            weekly_ranking_max=_parse_optional_int(weekly_ranking_max),
            daily_change_min=_parse_optional_int(daily_change_min),
            daily_change_max=_parse_optional_int(daily_change_max),
            weekly_change_min=_parse_optional_int(weekly_change_min),
            weekly_change_max=_parse_optional_int(weekly_change_max),
            click_share_min=_parse_optional_float(click_share_min),
            click_share_max=_parse_optional_float(click_share_max),
            conversion_share_min=_parse_optional_float(conversion_share_min),
            conversion_share_max=_parse_optional_float(conversion_share_max),
            conversion_rate_min=_parse_optional_float(conversion_rate_min),
            conversion_rate_max=_parse_optional_float(conversion_rate_max),
            is_new_day=_parse_optional_bool(is_new_day),
            is_new_week=_parse_optional_bool(is_new_week)
        )

        # 获取总数（应用筛选条件后）
        total_count = query.count()

        # 应用排序和分页
        items = query.order_by(asc(AmazonOriginSearchData.current_rangking_day)).offset(skip).limit(perPage).all()

        # 格式化数据
        formatted_data = [_format_search_data(item) for item in items]

        # 返回标准AMIS格式
        return {
            "status": 0,
            "msg": "查询成功",
            "data": {
                "items": formatted_data,
                "count": total_count,
                "page": page,
                "perPage": perPage
            }
        }

    except Exception as e:
        logger.error(f"搜索数据失败: {e}")
        return {
            "status": 1,
            "msg": f"查询失败: {str(e)}",
            "data": {
                "items": [],
                "count": 0,
                "page": page,
                "perPage": perPage
            }
        }


def _apply_search_filters(
        query,
        keyword: Optional[str] = None,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        asin: Optional[str] = None,
        product_title: Optional[str] = None,
        report_date: Optional[str] = None,
        daily_ranking_min: Optional[int] = None,
        daily_ranking_max: Optional[int] = None,
        weekly_ranking_min: Optional[int] = None,
        weekly_ranking_max: Optional[int] = None,
        daily_change_min: Optional[int] = None,
        daily_change_max: Optional[int] = None,
        weekly_change_min: Optional[int] = None,
        weekly_change_max: Optional[int] = None,
        click_share_min: Optional[float] = None,
        click_share_max: Optional[float] = None,
        conversion_share_min: Optional[float] = None,
        conversion_share_max: Optional[float] = None,
        conversion_rate_min: Optional[float] = None,
        conversion_rate_max: Optional[float] = None,
        is_new_day: Optional[bool] = None,
        is_new_week: Optional[bool] = None
):
    """应用搜索筛选条件"""

    # 基础搜索条件 - 过滤空字符串
    if keyword and keyword.strip():
        query = query.filter(AmazonOriginSearchData.keyword.ilike(f"%{keyword.strip()}%"))

    if brand and brand.strip():
        query = query.filter(AmazonOriginSearchData.top_brand.ilike(f"%{brand.strip()}%"))

    if category and category.strip():
        query = query.filter(AmazonOriginSearchData.top_category.ilike(f"%{category.strip()}%"))

    if asin and asin.strip():
        query = query.filter(AmazonOriginSearchData.top_product_asin.ilike(f"%{asin.strip()}%"))

    if product_title and product_title.strip():
        query = query.filter(AmazonOriginSearchData.top_product_title.ilike(f"%{product_title.strip()}%"))

    # 报告日期筛选
    if report_date and report_date.strip():
        try:
            target_date = datetime.strptime(report_date.strip(), "%Y-%m-%d").date()
            query = query.filter(
                or_(
                    AmazonOriginSearchData.report_date_day == target_date,
                    AmazonOriginSearchData.report_date_week == target_date
                )
            )
        except ValueError:
            logger.warning(f"无效的日期格式: {report_date}")

    # 排名范围筛选
    if daily_ranking_min is not None:
        query = query.filter(AmazonOriginSearchData.current_rangking_day >= daily_ranking_min)
    if daily_ranking_max is not None:
        query = query.filter(AmazonOriginSearchData.current_rangking_day <= daily_ranking_max)

    if weekly_ranking_min is not None:
        query = query.filter(AmazonOriginSearchData.current_rangking_week >= weekly_ranking_min)
    if weekly_ranking_max is not None:
        query = query.filter(AmazonOriginSearchData.current_rangking_week <= weekly_ranking_max)

    # 变化范围筛选
    if daily_change_min is not None:
        query = query.filter(AmazonOriginSearchData.ranking_change_day >= daily_change_min)
    if daily_change_max is not None:
        query = query.filter(AmazonOriginSearchData.ranking_change_day <= daily_change_max)

    if weekly_change_min is not None:
        query = query.filter(AmazonOriginSearchData.ranking_change_week >= weekly_change_min)
    if weekly_change_max is not None:
        query = query.filter(AmazonOriginSearchData.ranking_change_week <= weekly_change_max)

    # 份额范围筛选
    if click_share_min is not None:
        query = query.filter(AmazonOriginSearchData.top_product_click_share >= click_share_min)
    if click_share_max is not None:
        query = query.filter(AmazonOriginSearchData.top_product_click_share <= click_share_max)

    if conversion_share_min is not None:
        query = query.filter(AmazonOriginSearchData.top_product_conversion_share >= conversion_share_min)
    if conversion_share_max is not None:
        query = query.filter(AmazonOriginSearchData.top_product_conversion_share <= conversion_share_max)

    # 转化率筛选 (计算字段: 转化份额/点击份额)
    if conversion_rate_min is not None or conversion_rate_max is not None:
        # 避免除零错误
        query = query.filter(AmazonOriginSearchData.top_product_click_share > 0)

        if conversion_rate_min is not None:
            query = query.filter(
                (AmazonOriginSearchData.top_product_conversion_share /
                 AmazonOriginSearchData.top_product_click_share * 100) >= conversion_rate_min
            )
        if conversion_rate_max is not None:
            query = query.filter(
                (AmazonOriginSearchData.top_product_conversion_share /
                 AmazonOriginSearchData.top_product_click_share * 100) <= conversion_rate_max
            )

    # 布尔值筛选
    if is_new_day is not None:
        query = query.filter(AmazonOriginSearchData.is_new_day == is_new_day)

    if is_new_week is not None:
        query = query.filter(AmazonOriginSearchData.is_new_week == is_new_week)

    return query


def _format_search_data(item: AmazonOriginSearchData) -> Dict[str, Any]:
    """格式化搜索数据"""
    try:
        # 计算转化率 (避免除零错误)
        conversion_rate = 0.0
        if item.top_product_click_share and item.top_product_click_share > 0:
            conversion_rate = round(
                (item.top_product_conversion_share / item.top_product_click_share) * 100, 2
            )

        return {
            "id": item.id,
            "keyword": item.keyword,

            # 排名数据
            "current_rangking_day": item.current_rangking_day,
            "previous_rangking_day": item.previous_rangking_day,
            "ranking_change_day": item.ranking_change_day,
            "current_rangking_week": item.current_rangking_week,
            "previous_rangking_week": item.previous_rangking_week,
            "ranking_change_week": item.ranking_change_week,

            # 趋势图数据 (JSON格式)
            "ranking_trend_day": item.ranking_trend_day or [],

            # 商品信息
            "top_brand": item.top_brand,
            "top_category": item.top_category,
            "top_product_asin": item.top_product_asin,
            "top_product_title": item.top_product_title,

            # 数据指标
            "top_product_click_share": float(item.top_product_click_share),
            "top_product_conversion_share": float(item.top_product_conversion_share),
            "conversion_rate": conversion_rate,

            # 状态标识
            "is_new_day": item.is_new_day,
            "is_new_week": item.is_new_week,

            # 日期信息
            "report_date_day": item.report_date_day.isoformat() if item.report_date_day else None,
            "report_date_week": item.report_date_week.isoformat() if item.report_date_week else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }

    except Exception as e:
        logger.error(f"格式化数据失败: {e}")
        return {
            "id": getattr(item, 'id', 0),
            "keyword": getattr(item, 'keyword', ''),
            "error": "数据格式化失败"
        }