import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, asc
from typing import List, Tuple
from datetime import datetime

from app.table.analysis.analysis_model import AmazonOriginSearchData
from app.table.search.search_schemas import AnalysisSearchRequest

logger = logging.getLogger(__name__)


class AnalysisCRUD:
    """分析数据CRUD操作类"""

    def __init__(self, db: Session):
        self.db = db

    def search_data_paginated(self, params: AnalysisSearchRequest) -> Tuple[List[AmazonOriginSearchData], int]:
        """分页搜索数据"""
        try:
            # 计算偏移量
            skip = (params.page - 1) * params.perPage

            # 构建查询
            query = self._build_search_query(params)

            # 获取总数
            total_count = query.count()

            # 应用排序和分页
            if params.orderBy:
                if params.orderDir == "desc":
                    query = query.order_by(desc(getattr(AmazonOriginSearchData, params.orderBy)))
                else:
                    query = query.order_by(asc(getattr(AmazonOriginSearchData, params.orderBy)))

            return query.offset(skip).limit(params.perPage).all(), total_count

        except Exception as e:
            logger.error(f"分页搜索数据失败: {e}")
            return [], 0

    def _build_search_query(self, params: AnalysisSearchRequest):
        """构建搜索查询"""
        query = self.db.query(AmazonOriginSearchData)

        # 基础搜索条件
        query = self._apply_basic_filters(query, params)
        # 排名范围筛选
        query = self._apply_ranking_filters(query, params)
        # 变化范围筛选
        query = self._apply_change_filters(query, params)
        # 份额和转化率筛选
        query = self._apply_share_filters(query, params)
        # 布尔值筛选
        query = self._apply_boolean_filters(query, params)

        return query

    def _apply_basic_filters(self, query, params: AnalysisSearchRequest):
        """应用基础搜索筛选条件"""
        if params.keyword and params.keyword.strip():
            query = query.filter(AmazonOriginSearchData.keyword.ilike(f"%{params.keyword.strip()}%"))

        if params.brand and params.brand.strip():
            query = query.filter(AmazonOriginSearchData.top_brand.ilike(f"%{params.brand.strip()}%"))

        if params.category and params.category.strip():
            query = query.filter(AmazonOriginSearchData.top_category.ilike(f"%{params.category.strip()}%"))

        if params.asin and params.asin.strip():
            query = query.filter(AmazonOriginSearchData.top_product_asin.ilike(f"%{params.asin.strip()}%"))

        if params.product_title and params.product_title.strip():
            query = query.filter(AmazonOriginSearchData.top_product_title.ilike(f"%{params.product_title.strip()}%"))

        # 报告日期筛选
        if params.report_date and params.report_date.strip():
            try:
                target_date = datetime.strptime(params.report_date.strip(), "%Y-%m-%d").date()
                query = query.filter(
                    or_(
                        AmazonOriginSearchData.report_date_day == target_date,
                        AmazonOriginSearchData.report_date_week == target_date
                    )
                )
            except ValueError:
                logger.warning(f"无效的日期格式: {params.report_date}")

        return query

    def _apply_ranking_filters(self, query, params: AnalysisSearchRequest):
        """应用排名范围筛选"""
        # 日排名范围
        if params.daily_ranking_min is not None:
            query = query.filter(AmazonOriginSearchData.current_rangking_day >= params.daily_ranking_min)
        if params.daily_ranking_max is not None:
            query = query.filter(AmazonOriginSearchData.current_rangking_day <= params.daily_ranking_max)

        # 周排名范围
        if params.weekly_ranking_min is not None:
            query = query.filter(AmazonOriginSearchData.current_rangking_week >= params.weekly_ranking_min)
        if params.weekly_ranking_max is not None:
            query = query.filter(AmazonOriginSearchData.current_rangking_week <= params.weekly_ranking_max)

        return query

    def _apply_change_filters(self, query, params: AnalysisSearchRequest):
        """应用变化范围筛选"""
        # 日变化范围
        if params.daily_change_min is not None:
            query = query.filter(AmazonOriginSearchData.ranking_change_day >= params.daily_change_min)
        if params.daily_change_max is not None:
            query = query.filter(AmazonOriginSearchData.ranking_change_day <= params.daily_change_max)

        # 周变化范围
        if params.weekly_change_min is not None:
            query = query.filter(AmazonOriginSearchData.ranking_change_week >= params.weekly_change_min)
        if params.weekly_change_max is not None:
            query = query.filter(AmazonOriginSearchData.ranking_change_week <= params.weekly_change_max)

        return query

    def _apply_share_filters(self, query, params: AnalysisSearchRequest):
        """应用份额和转化率筛选"""
        # 点击份额范围
        if params.click_share_min is not None:
            query = query.filter(AmazonOriginSearchData.top_product_click_share >= params.click_share_min)
        if params.click_share_max is not None:
            query = query.filter(AmazonOriginSearchData.top_product_click_share <= params.click_share_max)

        # 转化份额范围
        if params.conversion_share_min is not None:
            query = query.filter(AmazonOriginSearchData.top_product_conversion_share >= params.conversion_share_min)
        if params.conversion_share_max is not None:
            query = query.filter(AmazonOriginSearchData.top_product_conversion_share <= params.conversion_share_max)

        # 转化率筛选 (计算字段: 转化份额/点击份额)
        if params.conversion_rate_min is not None or params.conversion_rate_max is not None:
            # 避免除零错误
            query = query.filter(AmazonOriginSearchData.top_product_click_share > 0)

            if params.conversion_rate_min is not None:
                query = query.filter(
                    (AmazonOriginSearchData.top_product_conversion_share /
                     AmazonOriginSearchData.top_product_click_share * 100) >= params.conversion_rate_min
                )
            if params.conversion_rate_max is not None:
                query = query.filter(
                    (AmazonOriginSearchData.top_product_conversion_share /
                     AmazonOriginSearchData.top_product_click_share * 100) <= params.conversion_rate_max
                )

        return query

    def _apply_boolean_filters(self, query, params: AnalysisSearchRequest):
        """应用布尔值筛选"""
        if params.is_new_day is not None:
            query = query.filter(AmazonOriginSearchData.is_new_day == params.is_new_day)

        if params.is_new_week is not None:
            query = query.filter(AmazonOriginSearchData.is_new_week == params.is_new_week)

        return query
