from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, update, insert
from typing import List, Dict, Any, Tuple
from datetime import date, timedelta
import logging
import asyncio

from ..models.search_data import AmazonOriginSearchData
from ..models.import_batch import ImportBatch
from ..config import settings

logger = logging.getLogger(__name__)


class AsyncBatchProcessor:
    """异步批次数据处理器 - SQLAlchemy 2.0 异步风格"""

    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session
        self.batch_size = settings.BATCH_SIZE
        self.max_workers = settings.MAX_WORKERS

    async def upsert_search_data_batch(
            self,
            data_batch: List[Dict[str, Any]],
            data_type: str
    ) -> Tuple[int, int]:
        """批量UPSERT搜索数据 - SQLAlchemy 2.0 异步版本"""
        try:
            logger.info(f"开始批量处理 {len(data_batch)} 条{data_type}数据")

            updated_count = 0
            inserted_count = 0

            # 分批处理以避免内存问题
            for i in range(0, len(data_batch), self.batch_size):
                batch_chunk = data_batch[i:i + self.batch_size]
                chunk_updated, chunk_inserted = await self._process_data_chunk(
                    batch_chunk, data_type
                )
                updated_count += chunk_updated
                inserted_count += chunk_inserted

                logger.debug(f"处理批次 {i // self.batch_size + 1}, 更新: {chunk_updated}, 插入: {chunk_inserted}")

            await self.async_session.commit()

            logger.info(f"批量处理完成，更新: {updated_count}, 插入: {inserted_count}")
            return updated_count, inserted_count

        except Exception as e:
            await self.async_session.rollback()
            logger.error(f"批量处理失败: {e}")
            raise

    async def _process_data_chunk(
            self,
            chunk: List[Dict[str, Any]],
            data_type: str
    ) -> Tuple[int, int]:
        """处理数据块 - SQLAlchemy 2.0 异步查询"""
        updated_count = 0
        inserted_count = 0

        try:
            # 提取所有ASIN用于批量查询
            asins = [record['top_product_asin'] for record in chunk if record.get('top_product_asin')]

            # SQLAlchemy 2.0 异步批量查询
            stmt = select(AmazonOriginSearchData).where(
                AmazonOriginSearchData.top_product_asin.in_(asins)
            )
            result = await self.async_session.execute(stmt)
            existing_records = {record.top_product_asin: record for record in result.scalars().all()}

            # 处理每条记录
            for record_data in chunk:
                asin = record_data.get('top_product_asin')
                if not asin:
                    continue

                existing_record = existing_records.get(asin)

                if existing_record:
                    # 更新现有记录
                    await self._update_existing_record(existing_record, record_data, data_type)
                    updated_count += 1
                else:
                    # 创建新记录
                    await self._create_new_record(record_data)
                    inserted_count += 1

            return updated_count, inserted_count

        except Exception as e:
            logger.error(f"处理数据块失败: {e}")
            raise

    async def _update_existing_record(
            self,
            existing_record: AmazonOriginSearchData,
            new_data: Dict[str, Any],
            data_type: str
    ):
        """更新现有记录 - SQLAlchemy 2.0 方式"""
        try:
            if data_type == 'daily':
                # 更新日数据字段
                existing_record.current_rangking_day = new_data.get('current_rangking_day',
                                                                    existing_record.current_rangking_day)
                existing_record.report_date_day = new_data.get('report_date_day', existing_record.report_date_day)
                existing_record.previous_rangking_day = existing_record.current_rangking_day  # 保存旧值
                existing_record.ranking_change_day = existing_record.current_rangking_day - existing_record.previous_rangking_day
                existing_record.is_new_day = True

                # 更新趋势数据
                trend_data = existing_record.ranking_trend_day or []
                trend_data.append({
                    'date': str(new_data.get('report_date_day')),
                    'ranking': new_data.get('current_rangking_day'),
                    'change': existing_record.ranking_change_day
                })
                # 只保留最近30天的趋势数据
                existing_record.ranking_trend_day = trend_data[-30:]

            elif data_type == 'weekly':
                # 更新周数据字段
                existing_record.current_rangking_week = new_data.get('current_rangking_week',
                                                                     existing_record.current_rangking_week)
                existing_record.report_date_week = new_data.get('report_date_week', existing_record.report_date_week)
                existing_record.previous_rangking_week = existing_record.current_rangking_week  # 保存旧值
                existing_record.ranking_change_week = existing_record.current_rangking_week - existing_record.previous_rangking_week
                existing_record.is_new_week = True

            # 更新共享字段（商品信息）
            existing_record.keyword = new_data.get('keyword', existing_record.keyword)
            existing_record.top_brand = new_data.get('top_brand', existing_record.top_brand)
            existing_record.top_category = new_data.get('top_category', existing_record.top_category)
            existing_record.top_product_title = new_data.get('top_product_title', existing_record.top_product_title)
            existing_record.top_product_click_share = new_data.get('top_product_click_share',
                                                                   existing_record.top_product_click_share)
            existing_record.top_product_conversion_share = new_data.get('top_product_conversion_share',
                                                                        existing_record.top_product_conversion_share)

            # SQLAlchemy 2.0 中，对象会自动标记为dirty，不需要显式add

        except Exception as e:
            logger.error(f"更新记录失败: {e}")
            raise

    async def _create_new_record(self, record_data: Dict[str, Any]):
        """创建新记录 - SQLAlchemy 2.0 方式"""
        try:
            new_record = AmazonOriginSearchData(**record_data)
            self.async_session.add(new_record)

        except Exception as e:
            logger.error(f"创建记录失败: {e}")
            raise

    async def bulk_upsert_optimized(
            self,
            data_batch: List[Dict[str, Any]],
            data_type: str
    ) -> Tuple[int, int]:
        """优化的批量UPSERT - 使用SQLAlchemy 2.0的高级功能"""
        try:
            # 分离更新和插入数据
            asins = [record['top_product_asin'] for record in data_batch if record.get('top_product_asin')]

            # 查询现有记录
            stmt = select(AmazonOriginSearchData.top_product_asin).where(
                AmazonOriginSearchData.top_product_asin.in_(asins)
            )
            result = await self.async_session.execute(stmt)
            existing_asins = set(row[0] for row in result.all())

            # 分离更新和插入数据
            update_data = []
            insert_data = []

            for record in data_batch:
                asin = record.get('top_product_asin')
                if asin in existing_asins:
                    update_data.append(record)
                else:
                    insert_data.append(record)

            updated_count = 0
            inserted_count = 0

            # 批量更新
            if update_data:
                updated_count = await self._bulk_update(update_data, data_type)

            # 批量插入
            if insert_data:
                inserted_count = await self._bulk_insert(insert_data)

            await self.async_session.commit()

            logger.info(f"优化批量处理完成，更新: {updated_count}, 插入: {inserted_count}")
            return updated_count, inserted_count

        except Exception as e:
            await self.async_session.rollback()
            logger.error(f"优化批量处理失败: {e}")
            raise

    async def _bulk_update(self, update_data: List[Dict[str, Any]], data_type: str) -> int:
        """批量更新 - SQLAlchemy 2.0 bulk update"""
        try:
            update_mappings = []

            for record in update_data:
                asin = record['top_product_asin']
                mapping = {'top_product_asin': asin}  # WHERE条件

                # 根据数据类型添加更新字段
                if data_type == 'daily':
                    mapping.update({
                        'current_rangking_day': record.get('current_rangking_day'),
                        'report_date_day': record.get('report_date_day'),
                        'is_new_day': True
                    })
                elif data_type == 'weekly':
                    mapping.update({
                        'current_rangking_week': record.get('current_rangking_week'),
                        'report_date_week': record.get('report_date_week'),
                        'is_new_week': True
                    })

                # 更新共享字段
                mapping.update({
                    'keyword': record.get('keyword'),
                    'top_brand': record.get('top_brand'),
                    'top_category': record.get('top_category'),
                    'top_product_title': record.get('top_product_title'),
                    'top_product_click_share': record.get('top_product_click_share'),
                    'top_product_conversion_share': record.get('top_product_conversion_share')
                })

                update_mappings.append(mapping)

            # SQLAlchemy 2.0 批量更新
            stmt = (
                update(AmazonOriginSearchData)
                .where(AmazonOriginSearchData.top_product_asin == update.bindparam('top_product_asin'))
            )

            # 设置更新值
            update_values = {}
            if data_type == 'daily':
                update_values.update({
                    'current_rangking_day': update.bindparam('current_rangking_day'),
                    'report_date_day': update.bindparam('report_date_day'),
                    'is_new_day': update.bindparam('is_new_day')
                })
            elif data_type == 'weekly':
                update_values.update({
                    'current_rangking_week': update.bindparam('current_rangking_week'),
                    'report_date_week': update.bindparam('report_date_week'),
                    'is_new_week': update.bindparam('is_new_week')
                })

            update_values.update({
                'keyword': update.bindparam('keyword'),
                'top_brand': update.bindparam('top_brand'),
                'top_category': update.bindparam('top_category'),
                'top_product_title': update.bindparam('top_product_title'),
                'top_product_click_share': update.bindparam('top_product_click_share'),
                'top_product_conversion_share': update.bindparam('top_product_conversion_share')
            })

            stmt = stmt.values(update_values)

            await self.async_session.execute(stmt, update_mappings)

            return len(update_mappings)

        except Exception as e:
            logger.error(f"批量更新失败: {e}")
            raise

    async def _bulk_insert(self, insert_data: List[Dict[str, Any]]) -> int:
        """批量插入 - SQLAlchemy 2.0 bulk insert"""
        try:
            # SQLAlchemy 2.0 批量插入
            stmt = insert(AmazonOriginSearchData)
            await self.async_session.execute(stmt, insert_data)

            return len(insert_data)

        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            raise

    async def cleanup_old_data(self, keep_days: int = 30) -> int:
        """清理旧数据 - SQLAlchemy 2.0 异步删除"""
        try:
            cutoff_date = date.today() - timedelta(days=keep_days)

            # SQLAlchemy 2.0 删除语句
            from sqlalchemy import delete

            stmt = delete(AmazonOriginSearchData).where(
                and_(
                    AmazonOriginSearchData.report_date_day < cutoff_date,
                    AmazonOriginSearchData.report_date_week < cutoff_date
                )
            )

            result = await self.async_session.execute(stmt)
            deleted_count = result.rowcount

            await self.async_session.commit()

            logger.info(f"清理了 {deleted_count} 条旧数据")
            return deleted_count

        except Exception as e:
            await self.async_session.rollback()
            logger.error(f"清理旧数据失败: {e}")
            raise