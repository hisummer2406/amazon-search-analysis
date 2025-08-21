import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from datetime import datetime, date

from database import get_db
from app.models.analysis_schemas import AmazonOriginSearchData
from app.dependencies.login_auth import get_current_user

logger = logging.getLogger(__name__)

analysis_router = APIRouter()


@analysis_router.get("/search")
async def search_data(
        # 分页参数
        page: int = Query(1, ge=1, description="页码"),
        perPage: int = Query(50, ge=1, le=200, description="每页数量"),

        # 搜索条件参数
        keyword: Optional[str] = Query(None, description="关键词搜索"),
        daily_ranking: Optional[str] = Query(None, description="日排名筛选"),
        daily_change: Optional[str] = Query(None, description="日变化筛选"),
        weekly_ranking: Optional[str] = Query(None, description="周排名筛选"),
        weekly_change: Optional[str] = Query(None, description="周变化筛选"),
        category: Optional[str] = Query(None, description="类目筛选"),
        weekly_weekly_change: Optional[str] = Query("ALL", description="周周变化筛选"),
        total_change: Optional[str] = Query(None, description="总变化筛选"),
        click_share: Optional[str] = Query(None, description="点击份额筛选"),
        conversion_share: Optional[str] = Query(None, description="转化份额筛选"),
        conversion_rate: Optional[str] = Query(None, description="转化率筛选"),
        is_new_day: Optional[str] = Query(None, description="是否日期新筛选"),
        is_new_week: Optional[str] = Query(None, description="是否周新数筛选"),
        has_weekly_daily: Optional[str] = Query(None, description="是否周有日一筛选"),
        report_date: Optional[str] = Query(None, description="日期筛选"),

        # 依赖注入
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """搜索亚马逊数据"""
    try:
        # 计算偏移量
        skip = (page - 1) * perPage

        # 构建查询
        query = db.query(AmazonOriginSearchData)

        # 应用筛选条件
        query = _apply_search_filters(
            query=query,
            keyword=keyword,
            daily_ranking=daily_ranking,
            daily_change=daily_change,
            weekly_ranking=weekly_ranking,
            weekly_change=weekly_change,
            category=category,
            weekly_weekly_change=weekly_weekly_change,
            total_change=total_change,
            click_share=click_share,
            conversion_share=conversion_share,
            conversion_rate=conversion_rate,
            is_new_day=is_new_day,
            is_new_week=is_new_week,
            has_weekly_daily=has_weekly_daily,
            report_date=report_date
        )

        # 获取总数（应用筛选条件后）
        total_count = query.count()

        # 应用排序和分页
        items = query.order_by(desc(AmazonOriginSearchData.created_at)).offset(skip).limit(perPage).all()

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
        daily_ranking: Optional[str] = None,
        daily_change: Optional[str] = None,
        weekly_ranking: Optional[str] = None,
        weekly_change: Optional[str] = None,
        category: Optional[str] = None,
        weekly_weekly_change: Optional[str] = None,
        total_change: Optional[str] = None,
        click_share: Optional[str] = None,
        conversion_share: Optional[str] = None,
        conversion_rate: Optional[str] = None,
        is_new_day: Optional[str] = None,
        is_new_week: Optional[str] = None,
        has_weekly_daily: Optional[str] = None,
        report_date: Optional[str] = None
):
    """应用搜索筛选条件"""

    # 关键词搜索
    if keyword:
        query = query.filter(AmazonOriginSearchData.keyword.ilike(f"%{keyword}%"))

    # 日排名筛选
    if daily_ranking and daily_ranking != "-":
        try:
            ranking_range = _parse_ranking_filter(daily_ranking)
            if ranking_range:
                min_val, max_val = ranking_range
                query = query.filter(
                    and_(
                        AmazonOriginSearchData.current_rangking_day >= min_val,
                        AmazonOriginSearchData.current_rangking_day <= max_val
                    )
                )
        except ValueError:
            pass

    # 日变化筛选
    if daily_change and daily_change != "-":
        try:
            change_range = _parse_change_filter(daily_change)
            if change_range:
                min_val, max_val = change_range
                query = query.filter(
                    and_(
                        AmazonOriginSearchData.ranking_change_day >= min_val,
                        AmazonOriginSearchData.ranking_change_day <= max_val
                    )
                )
        except ValueError:
            pass

    # 周排名筛选
    if weekly_ranking and weekly_ranking != "-":
        try:
            ranking_range = _parse_ranking_filter(weekly_ranking)
            if ranking_range:
                min_val, max_val = ranking_range
                query = query.filter(
                    and_(
                        AmazonOriginSearchData.current_rangking_week >= min_val,
                        AmazonOriginSearchData.current_rangking_week <= max_val
                    )
                )
        except ValueError:
            pass

    # 周变化筛选
    if weekly_change and weekly_change != "-":
        try:
            change_range = _parse_change_filter(weekly_change)
            if change_range:
                min_val, max_val = change_range
                query = query.filter(
                    and_(
                        AmazonOriginSearchData.ranking_change_week >= min_val,
                        AmazonOriginSearchData.ranking_change_week <= max_val
                    )
                )
        except ValueError:
            pass

    # 类目筛选
    if category and category != "全部":
        query = query.filter(AmazonOriginSearchData.top_category.ilike(f"%{category}%"))

    # 点击份额筛选
    if click_share and click_share != "-":
        try:
            share_range = _parse_numeric_filter(click_share)
            if share_range:
                min_val, max_val = share_range
                query = query.filter(
                    and_(
                        AmazonOriginSearchData.top_product_click_share >= min_val,
                        AmazonOriginSearchData.top_product_click_share <= max_val
                    )
                )
        except ValueError:
            pass

    # 转化份额筛选
    if conversion_share and conversion_share != "-":
        try:
            share_range = _parse_numeric_filter(conversion_share)
            if share_range:
                min_val, max_val = share_range
                query = query.filter(
                    and_(
                        AmazonOriginSearchData.top_product_conversion_share >= min_val,
                        AmazonOriginSearchData.top_product_conversion_share <= max_val
                    )
                )
        except ValueError:
            pass

    # 转化率筛选 (计算字段: 转化份额/点击份额)
    if conversion_rate and conversion_rate != "-":
        try:
            rate_range = _parse_numeric_filter(conversion_rate)
            if rate_range:
                min_val, max_val = rate_range
                # 避免除零错误
                query = query.filter(
                    and_(
                        AmazonOriginSearchData.top_product_click_share > 0,
                        (AmazonOriginSearchData.top_product_conversion_share /
                         AmazonOriginSearchData.top_product_click_share) >= min_val,
                        (AmazonOriginSearchData.top_product_conversion_share /
                         AmazonOriginSearchData.top_product_click_share) <= max_val
                    )
                )
        except ValueError:
            pass

    # 是否日新品筛选
    if is_new_day and is_new_day != "-":
        is_new = is_new_day.lower() in ["true", "是", "1", "yes"]
        query = query.filter(AmazonOriginSearchData.is_new_day == is_new)

    # 是否周新品筛选
    if is_new_week and is_new_week != "-":
        is_new = is_new_week.lower() in ["true", "是", "1", "yes"]
        query = query.filter(AmazonOriginSearchData.is_new_week == is_new)

    # 日期筛选
    if report_date:
        try:
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
            query = query.filter(
                or_(
                    AmazonOriginSearchData.report_date_day == target_date,
                    AmazonOriginSearchData.report_date_week == target_date
                )
            )
        except ValueError:
            pass

    return query


def _parse_ranking_filter(ranking_str: str) -> Optional[tuple]:
    """解析排名筛选条件
    例如: "1-10", ">100", "<50", "=1"
    """
    if not ranking_str or ranking_str == "-":
        return None

    try:
        if "-" in ranking_str and not ranking_str.startswith("-"):
            # 范围筛选: "1-10"
            parts = ranking_str.split("-")
            if len(parts) == 2:
                min_val = int(parts[0])
                max_val = int(parts[1])
                return (min_val, max_val)
        elif ranking_str.startswith(">"):
            # 大于筛选: ">100"
            val = int(ranking_str[1:])
            return (val + 1, 999999)
        elif ranking_str.startswith("<"):
            # 小于筛选: "<50"
            val = int(ranking_str[1:])
            return (1, val - 1)
        elif ranking_str.startswith("="):
            # 等于筛选: "=1"
            val = int(ranking_str[1:])
            return (val, val)
        else:
            # 直接数字: "10"
            val = int(ranking_str)
            return (val, val)
    except ValueError:
        return None

    return None


def _parse_change_filter(change_str: str) -> Optional[tuple]:
    """解析变化筛选条件
    例如: "-10到10", ">50", "<-20", "=0"
    """
    if not change_str or change_str == "-":
        return None

    try:
        if "到" in change_str:
            # 范围筛选: "-10到10"
            parts = change_str.split("到")
            if len(parts) == 2:
                min_val = int(parts[0])
                max_val = int(parts[1])
                return (min_val, max_val)
        elif change_str.startswith(">"):
            # 大于筛选: ">50"
            val = int(change_str[1:])
            return (val + 1, 999999)
        elif change_str.startswith("<"):
            # 小于筛选: "<-20"
            val = int(change_str[1:])
            return (-999999, val - 1)
        elif change_str.startswith("="):
            # 等于筛选: "=0"
            val = int(change_str[1:])
            return (val, val)
        else:
            # 直接数字: "10"
            val = int(change_str)
            return (val, val)
    except ValueError:
        return None

    return None


def _parse_numeric_filter(numeric_str: str) -> Optional[tuple]:
    """解析数值筛选条件 (用于份额、转化率等)
    例如: "0.1-0.5", ">0.3", "<0.2", "=0.15"
    """
    if not numeric_str or numeric_str == "-":
        return None

    try:
        if "-" in numeric_str and not numeric_str.startswith("-"):
            # 范围筛选: "0.1-0.5"
            parts = numeric_str.split("-")
            if len(parts) == 2:
                min_val = float(parts[0])
                max_val = float(parts[1])
                return (min_val, max_val)
        elif numeric_str.startswith(">"):
            # 大于筛选: ">0.3"
            val = float(numeric_str[1:])
            return (val, 999999.0)
        elif numeric_str.startswith("<"):
            # 小于筛选: "<0.2"
            val = float(numeric_str[1:])
            return (0.0, val)
        elif numeric_str.startswith("="):
            # 等于筛选: "=0.15"
            val = float(numeric_str[1:])
            return (val, val)
        else:
            # 直接数字: "0.25"
            val = float(numeric_str)
            return (val, val)
    except ValueError:
        return None

    return None


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