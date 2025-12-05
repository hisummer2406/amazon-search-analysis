import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, asc
from typing import List, Tuple
from datetime import datetime

from sqlalchemy import desc, or_, asc, func, and_, text, select

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

            # 构建基础查询
            base_query = self._build_search_query(params)

            # 仅第一页或少量数据时精确统计
            if self._has_user_filters(params) and params.page == 1:
                total_count = base_query.count()
            elif self._has_user_filters(params):
                # 后续页使用limit估算（避免全表扫描）
                total_count = base_query.limit(10000).count()
            else:
                total_count = self._get_table_estimate_count()

            # 应用排序和分页到完整查询
            result_query = base_query
            if params.orderBy:
                if params.orderDir == "desc":
                    result_query = result_query.order_by(desc(getattr(AmazonOriginSearchData, params.orderBy)))
                else:
                    result_query = result_query.order_by(asc(getattr(AmazonOriginSearchData, params.orderBy)))
            else:
                result_query = result_query.order_by(
                    desc(AmazonOriginSearchData.report_date_day),
                    asc(AmazonOriginSearchData.current_rangking_day)
                )

            results = result_query.offset(skip).limit(params.perPage).all()

            return results, total_count

        except Exception as e:
            logger.error(f"分页搜索数据失败: {e}")
            return [], 0

    def get_categories(self) -> List[dict]:
        """获取类目列表 - 使用视图查询"""
        try:
            result = self.db.execute(
                text("SELECT top_category, cnt FROM analysis.my_category_stats ORDER BY cnt DESC")
            ).fetchall()

            return [
                {
                    "label": f"{row.top_category} ({row.cnt})",
                    "value": row.top_category
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"获取类目列表失败: {e}")
            return []

    def _has_user_filters(self, params: AnalysisSearchRequest) -> bool:
        """判断是否有用户搜索条件（排除默认过滤）"""
        return any([
            # 基础搜索
            params.keyword, params.brand, params.category,
            params.asin, params.product_title, params.report_date,
            # 排名范围
            params.daily_ranking_min is not None, params.daily_ranking_max is not None,
            params.weekly_ranking_min is not None, params.weekly_ranking_max is not None,
            # 变化范围
            params.daily_change_min is not None, params.daily_change_max is not None,
            params.weekly_change_min is not None, params.weekly_change_max is not None,
            # 份额转化率
            params.click_share_min is not None, params.click_share_max is not None,
            params.conversion_share_min is not None, params.conversion_share_max is not None,
            params.conversion_rate_min is not None, params.conversion_rate_max is not None,
            # 布尔值
            params.is_new_day is not None, params.is_new_week is not None
        ])

    def _get_table_estimate_count(self) -> int:
        """使用PG统计信息快速估算总行数"""
        try:
            result = self.db.execute(
                text("""
                     SELECT reltuples::bigint AS estimate
                     FROM pg_class
                     WHERE relname = :table_name
                       AND relnamespace = (SELECT oid
                                           FROM pg_namespace
                                           WHERE nspname = :schema_name)
                     """),
                {"table_name": "amazon_origin_search_data", "schema_name": "analysis"}
            ).scalar()
            return result or 0
        except Exception as e:
            logger.error(f"估算表行数失败: {e}")
            return 0

    def _build_search_query(self, params: AnalysisSearchRequest):
        """构建搜索查询"""
        query = self.db.query(AmazonOriginSearchData)

        # 默认过滤条件：排除关键词中包含品牌词的条目
        query = query.filter(
            and_(
                AmazonOriginSearchData.top_brand.isnot(None),
                AmazonOriginSearchData.top_brand != '',
                ~func.lower(AmazonOriginSearchData.keyword).like(
                    func.concat('%', func.lower(AmazonOriginSearchData.top_brand), '%')
                )
            )
        )

        # 基础过滤：排除日排名为0的数据
        query = query.filter(AmazonOriginSearchData.current_rangking_day != 0)

        # 新增：过滤黑名单类目
        query = query.filter(
            ~AmazonOriginSearchData.top_category.in_([
                'Books',
                'Grocery',
                'Video Games',
                'Digital_Video_Download',
                'Digital_Ebook_Purchase',
                'Digital_Music_Purchase'
            ])
        )

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
