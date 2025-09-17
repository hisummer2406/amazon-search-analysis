import logging
from sqlalchemy.orm import Session
from typing import List

from app.table.analysis.analysis_crud import AnalysisCRUD
from app.table.analysis.analysis_model import AmazonOriginSearchData
from app.table.search.search_schemas import (
    AnalysisSearchRequest,
    AnalysisSearchResponse,
    AnalysisDataItem,
    PaginationData
)

logger = logging.getLogger(__name__)


class AnalysisService:
    """分析数据业务逻辑服务"""

    def __init__(self, db: Session):
        self.db = db
        self.crud = AnalysisCRUD(db)

    def search_data(self, params: AnalysisSearchRequest) -> AnalysisSearchResponse:
        """搜索分析数据"""
        try:
            # 调用CRUD层获取数据
            items, total_count = self.crud.search_data_paginated(params)

            # 格式化数据
            formatted_items = [self._format_data_item(item) for item in items]

            # 构建分页数据
            pagination_data = PaginationData(
                items=formatted_items,
                count=total_count,
                page=params.page,
                perPage=params.perPage
            )

            return AnalysisSearchResponse(
                status=0,
                msg="查询成功",
                data=pagination_data.model_dump()
            )

        except Exception as e:
            logger.error(f"搜索数据服务失败: {e}")
            return AnalysisSearchResponse(
                status=1,
                msg=f"查询失败: {str(e)}",
                data={
                    "items": [],
                    "count": 0,
                    "page": params.page,
                    "perPage": params.perPage
                }
            )

    def get_categories(self) -> List[dict]:
        """获取类目选项"""
        return self.crud.get_categories()

    def _format_data_item(self, item: AmazonOriginSearchData) -> AnalysisDataItem:
        """格式化单个数据项"""
        try:
            # 计算转化率 (避免除零错误)
            conversion_rate = 0.0
            if item.top_product_click_share and item.top_product_click_share > 0:
                conversion_rate = round(
                    (item.top_product_conversion_share / item.top_product_click_share) * 100, 2
                )

            return AnalysisDataItem(
                id=item.id,
                keyword=item.keyword,

                # 排名数据
                current_rangking_day=item.current_rangking_day,
                previous_rangking_day=item.previous_rangking_day,
                ranking_change_day=item.ranking_change_day,
                current_rangking_week=item.current_rangking_week,
                previous_rangking_week=item.previous_rangking_week,
                ranking_change_week=item.ranking_change_week,

                # 趋势图数据
                ranking_trend_day=item.ranking_trend_day or [],

                # 商品信息
                top_brand=item.top_brand,
                top_category=item.top_category,
                top_product_asin=item.top_product_asin,
                top_product_title=item.top_product_title,

                # 数据指标
                top_product_click_share=float(item.top_product_click_share),
                top_product_conversion_share=float(item.top_product_conversion_share),
                conversion_rate=conversion_rate,

                # 状态标识
                is_new_day=item.is_new_day,
                is_new_week=item.is_new_week,

                # 日期信息
                report_date_day=item.report_date_day.isoformat() if item.report_date_day else None,
                report_date_week=item.report_date_week.isoformat() if item.report_date_week else None,
                created_at=item.created_at.isoformat() if item.created_at else None,
            )

        except Exception as e:
            logger.error(f"格式化数据项失败: {e}")
            # 返回基础数据项，避免整个请求失败
            return AnalysisDataItem(
                id=getattr(item, 'id', 0),
                keyword=getattr(item, 'keyword', ''),
                current_rangking_day=0,
                previous_rangking_day=0,
                ranking_change_day=0,
                current_rangking_week=0,
                previous_rangking_week=0,
                ranking_change_week=0,
                top_brand="",
                top_category="",
                top_product_asin="",
                top_product_title="",
                top_product_click_share=0.0,
                top_product_conversion_share=0.0,
                conversion_rate=0.0,
                is_new_day=False,
                is_new_week=False
            )

