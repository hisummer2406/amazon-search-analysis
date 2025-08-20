from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, desc, func
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import logging

from app.models.search_data import AmazonOriginSearchData
from app.models.import_batch import ImportBatch
from app.schemas.import_batch import ImportBatchCreate, ImportBatchUpdate, BatchStatus
from app.config import settings

logger = logging.getLogger(__name__)

class BatchManager:
    """批次管理服务"""

    def __init__(self, db: Session):
        self.db = db
        self.batch_size = settings.BATCH_SIZE

    def create_batch(
            self,
            batch_data: ImportBatchCreate
    ) -> ImportBatch:
        """创建新的导入批次"""
        try:
            db_batch = ImportBatch(**batch_data.dict())
            self.db.add(db_batch)
            self.db.commit()
            self.db.refresh(db_batch)

            logger.info(f"创建批次成功: {db_batch.id}")
            return db_batch

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建批次失败: {e}")
            raise

    def update_batch(
            self,
            batch_id: int,
            update_data: Dict[str, Any]  # 改为更灵活的字典类型
    ) -> Optional[ImportBatch]:
        """更新批次信息"""
        try:
            db_batch = self.db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
            if not db_batch:
                return None

            for key, value in update_data.items():
                if hasattr(db_batch, key):
                    setattr(db_batch, key, value)

            self.db.commit()
            self.db.refresh(db_batch)

            logger.info(f"更新批次成功: {batch_id}")
            return db_batch

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新批次失败: {e}")
            raise

    def get_recent_batches(self, days: int = 7) -> List[ImportBatch]:
        """获取最近N天的批次"""
        try:
            cutoff_date = date.today() - timedelta(days=days)

            batches = self.db.query(ImportBatch).filter(
                ImportBatch.import_date >= cutoff_date
            ).order_by(desc(ImportBatch.import_date)).all()

            return batches

        except Exception as e:
            logger.error(f"获取最近批次失败: {e}")
            return []

    def get_recent_import_dates(self, days: int = 7) -> List[date]:
        """获取最近N天的导入日期"""
        try:
            cutoff_date = date.today() - timedelta(days=days)

            dates = self.db.query(ImportBatch.import_date).filter(
                and_(
                    ImportBatch.import_date >= cutoff_date,
                    ImportBatch.status == BatchStatus.COMPLETED
                )
            ).distinct().order_by(desc(ImportBatch.import_date)).all()

            return [d[0] for d in dates]

        except Exception as e:
            logger.error(f"获取最近导入日期失败: {e}")
            return []

    def get_batch_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取批次统计信息"""
        try:
            cutoff_date = date.today() - timedelta(days=days)

            # 总批次数
            total_batches = self.db.query(func.count(ImportBatch.id)).filter(
                ImportBatch.import_date >= cutoff_date
            ).scalar()

            # 成功批次数
            successful_batches = self.db.query(func.count(ImportBatch.id)).filter(
                and_(
                    ImportBatch.import_date >= cutoff_date,
                    ImportBatch.status == BatchStatus.COMPLETED
                )
            ).scalar()

            # 失败批次数
            failed_batches = self.db.query(func.count(ImportBatch.id)).filter(
                and_(
                    ImportBatch.import_date >= cutoff_date,
                    ImportBatch.status == BatchStatus.FAILED
                )
            ).scalar()

            # 处理中批次数
            processing_batches = self.db.query(func.count(ImportBatch.id)).filter(
                and_(
                    ImportBatch.import_date >= cutoff_date,
                    ImportBatch.status == BatchStatus.PROCESSING
                )
            ).scalar()

            # 总处理记录数
            total_records = self.db.query(func.sum(ImportBatch.total_raw_records)).filter(
                and_(
                    ImportBatch.import_date >= cutoff_date,
                    ImportBatch.status == BatchStatus.COMPLETED
                )
            ).scalar() or 0

            # 平均处理时间
            avg_time = self.db.query(func.avg(ImportBatch.processing_time_seconds)).filter(
                and_(
                    ImportBatch.import_date >= cutoff_date,
                    ImportBatch.status == BatchStatus.COMPLETED
                )
            ).scalar() or 0

            return {
                'total_batches': total_batches or 0,
                'successful_batches': successful_batches or 0,
                'failed_batches': failed_batches or 0,
                'processing_batches': processing_batches or 0,
                'total_records_processed': total_records,
                'avg_processing_time': float(avg_time),
                'success_rate': (successful_batches / total_batches * 100) if total_batches > 0 else 0
            }

        except Exception as e:
            logger.error(f"获取批次统计失败: {e}")
            return {}

    def create_batch(
            self,
            batch_data: ImportBatchCreate
    ) -> ImportBatch:
        """创建新的导入批次"""
        try:
            db_batch = ImportBatch(**batch_data.dict())
            self.db.add(db_batch)
            self.db.commit()
            self.db.refresh(db_batch)

            logger.info(f"创建批次成功: {db_batch.id}")
            return db_batch

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建批次失败: {e}")
            raise

    def update_batch(
            self,
            batch_id: int,
            update_data: ImportBatchUpdate
    ) -> Optional[ImportBatch]:
        """更新批次信息"""
        try:
            db_batch = self.db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
            if not db_batch:
                return None

            for key, value in update_data.dict(exclude_unset=True).items():
                setattr(db_batch, key, value)

            self.db.commit()
            self.db.refresh(db_batch)

            logger.info(f"更新批次成功: {batch_id}")
            return db_batch

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新批次失败: {e}")
            raise

    def get_recent_batches(self, days: int = 7) -> List[ImportBatch]:
        """获取最近N天的批次"""
        try:
            cutoff_date = date.today() - timedelta(days=days)

            batches = self.db.query(ImportBatch).filter(
                ImportBatch.import_date >= cutoff_date
            ).order_by(desc(ImportBatch.import_date)).all()

            return batches

        except Exception as e:
            logger.error(f"获取最近批次失败: {e}")
            return []

    def get_recent_import_dates(self, days: int = 7) -> List[date]:
        """获取最近N天的导入日期"""
        try:
            cutoff_date = date.today() - timedelta(days=days)

            dates = self.db.query(ImportBatch.import_date).filter(
                and_(
                    ImportBatch.import_date >= cutoff_date,
                    ImportBatch.status == BatchStatus.COMPLETED
                )
            ).distinct().order_by(desc(ImportBatch.import_date)).all()

            return [d[0] for d in dates]

        except Exception as e:
            logger.error(f"获取最近导入日期失败: {e}")
            return []


class AsyncBatchProcessor:
    """异步批次数据处理器"""

    def __init__(self, async_db: AsyncSession):
        self.async_db = async_db
        self.batch_size = settings.BATCH_SIZE
        self.max_workers = settings.MAX_WORKERS

    async def upsert_search_data_batch(
            self,
            data_batch: List[Dict[str, Any]],
            data_type: str
    ) -> Tuple[int, int]:
        """批量UPSERT搜索数据"""
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

            await self.async_db.commit()

            logger.info(f"批量处理完成，更新: {updated_count}, 插入: {inserted_count}")
            return updated_count, inserted_count

        except Exception as e:
            await self.async_db.rollback()
            logger.error(f"批量处理失败: {e}")
            raise

    async def _process_data_chunk(
            self,
            chunk: List[Dict[str, Any]],
            data_type: str
    ) -> Tuple[int, int]:
        """处理数据块"""
        updated_count = 0
        inserted_count = 0

        try:
            # 提取所有ASIN用于批量查询
            asins = [record['top_product_asin'] for record in chunk if record.get('top_product_asin')]

            # 批量查询现有记录
            stmt = select(AmazonOriginSearchData).where(
                AmazonOriginSearchData.top_product_asin.in_(asins)
            )
            result = await self.async_db.execute(stmt)
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
        """更新现有记录"""
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

            # 不需要显式调用add，因为对象已经在session中

        except Exception as e:
            logger.error(f"更新记录失败: {e}")
            raise

    async def _create_new_record(self, record_data: Dict[str, Any]):
        """创建新记录"""
        try:
            new_record = AmazonOriginSearchData(**record_data)
            self.async_db.add(new_record)

        except Exception as e:
            logger.error(f"创建记录失败: {e}")
            raise

    async def cleanup_old_data(self, keep_days: int = 30):
        """清理旧数据"""
        try:
            cutoff_date = date.today() - timedelta(days=keep_days)

            # 删除超过保留期的数据
            stmt = select(AmazonOriginSearchData).where(
                and_(
                    AmazonOriginSearchData.report_date_day < cutoff_date,
                    AmazonOriginSearchData.report_date_week < cutoff_date
                )
            )
            result = await self.async_db.execute(stmt)
            old_records = result.scalars().all()

            for record in old_records:
                await self.async_db.delete(record)

            await self.async_db.commit()

            logger.info(f"清理了 {len(old_records)} 条旧数据")
            return len(old_records)

        except Exception as e:
            await self.async_db.rollback()
            logger.error(f"清理旧数据失败: {e}")
            raise