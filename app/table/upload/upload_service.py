import asyncio
import logging
import os
import re
import tempfile
from concurrent.futures import ProcessPoolExecutor
from typing import Tuple, Optional, List
from datetime import datetime, date
from pathlib import Path
from sqlalchemy.orm import Session

from app.table.upload.import_model import ImportBatchRecords, StatusEnum
from app.table.upload.csv_processor import CSVProcessor, validate_csv_structure
from config import settings

logger = logging.getLogger(__name__)


def _process_chunk_worker(chunk_file: str, report_date_str: str, data_type: str, chunk_id: int) -> dict:
    """独立工作进程 - 处理单个分片文件"""
    try:
        from datetime import date
        from database import SessionFactory
        from app.table.upload.csv_processor import CSVProcessor

        report_date = date.fromisoformat(report_date_str)
        processor = CSVProcessor(batch_size=settings.BATCH_SIZE)
        processed_count = 0

        # 独立数据库会话
        with SessionFactory() as db_session:
            for chunk_df in processor.read_csv_chunks(chunk_file):
                chunk_processed = processor.process_chunk_with_upsert(
                    chunk_df, report_date, data_type, db_session
                )
                processed_count += chunk_processed

        # 清理分片文件
        if os.path.exists(chunk_file):
            os.unlink(chunk_file)

        return {'chunk_id': chunk_id, 'processed_count': processed_count, 'status': 'success'}

    except Exception as e:
        # 确保清理文件
        if os.path.exists(chunk_file):
            os.unlink(chunk_file)
        return {'chunk_id': chunk_id, 'processed_count': 0, 'status': 'failed', 'error': str(e)}


class UploadService:
    """CSV文件上传处理服务"""

    def __init__(self, db: Session):
        self.db = db
        self.csv_processor = CSVProcessor(batch_size=settings.BATCH_SIZE)
        self.max_workers = max(settings.MAX_WORKERS, os.cpu_count())
        self.multiprocess_threshold = settings.MULTIPROCESSING_THRESHOLD_MB * 1024 * 1024

    async def process_csv_file(
            self, file_path: str, original_filename: str, data_type: str
    ) -> Tuple[bool, str, Optional[ImportBatchRecords]]:
        """选择处理策略：大文件多进程，小文件单线程"""

        # 1. 验证文件结构
        is_valid, validation_message = validate_csv_structure(file_path)
        if not is_valid:
            return False, validation_message, None

        # 2. 获取文件大小，决定处理策略
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        logger.info(f"文件: {original_filename}, 大小: {file_size_mb:.1f}MB")

        if file_size >= self.multiprocess_threshold:
            logger.info(f"使用多进程处理大文件: {file_size_mb:.1f}MB")
            return await self._process_with_multiprocessing(file_path, original_filename, data_type)
        else:
            logger.info(f"使用单线程处理小文件: {file_size_mb:.1f}MB")
            return await self._process_with_single_thread(file_path, original_filename, data_type)

    async def _process_with_single_thread(
            self, file_path: str, original_filename: str, data_type: str
    ) -> Tuple[bool, str, Optional[ImportBatchRecords]]:
        """单线程处理小文件"""
        batch_record = None
        try:
            # 解析文件名获取报告日期
            report_date = self._extract_date_from_filename(original_filename)
            if not report_date:
                return False, "无法从文件名中解析出日期", None

            # 获取文件信息
            file_info = self.csv_processor.get_file_info(file_path)

            # 创建导入批次记录
            batch_record = self._create_batch_record(
                original_filename, report_date, file_info['estimated_records'],
                data_type == 'daily', data_type == 'weekly'
            )

            logger.info(f"开始单线程处理: {original_filename}, 预估记录数: {file_info['estimated_records']}")

            # 处理CSV文件
            success, message = await self._process_csv_with_upsert(
                file_path, batch_record, report_date, data_type
            )

            if success:
                batch_record.status = StatusEnum.COMPLETED
                batch_record.completed_at = datetime.now()
                processing_seconds = int(
                    (datetime.now() - batch_record.created_at.replace(tzinfo=None)).total_seconds())
                batch_record.processing_seconds = processing_seconds
                self.db.commit()
                logger.info(f"单线程处理完成: {original_filename}, 耗时: {processing_seconds}秒")

            return success, message, batch_record

        except Exception as e:
            logger.error(f"单线程处理失败: {e}")
            if batch_record:
                self._update_batch_record_error(batch_record, str(e))
            return False, f"文件处理失败: {str(e)}", batch_record

    async def _process_with_multiprocessing(
            self, file_path: str, original_filename: str, data_type: str
    ) -> Tuple[bool, str, Optional[ImportBatchRecords]]:
        """多进程处理大文件"""
        batch_record = None
        temp_dir = None
        start_time = datetime.now()

        try:
            # 1. 初始化
            report_date = self._extract_date_from_filename(original_filename)
            if not report_date:
                return False, "无法解析文件日期", None

            file_info = self.csv_processor.get_file_info(file_path)
            batch_record = self._create_batch_record(
                original_filename, report_date, file_info['estimated_records'],
                data_type == 'daily', data_type == 'weekly'
            )

            # 2. 文件分片
            temp_dir = tempfile.mkdtemp(prefix="upload_")
            chunk_files = await self._split_file_by_lines(file_path, temp_dir, settings.FILE_SPLIT_LINES)
            logger.info(f"文件分片完成: {len(chunk_files)} 个分片")

            # 3. 并行处理
            loop = asyncio.get_event_loop()
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                tasks = [
                    loop.run_in_executor(executor, _process_chunk_worker, chunk_file, str(report_date), data_type, i)
                    for i, chunk_file in enumerate(chunk_files)
                ]

                # 启动进度监控
                monitor_task = asyncio.create_task(self._monitor_progress(batch_record, start_time))
                results = await asyncio.gather(*tasks, return_exceptions=True)
                monitor_task.cancel()

            # 4. 统计结果
            total_processed = sum(r.get('processed_count', 0) for r in results if isinstance(r, dict))
            failed_count = sum(1 for r in results if isinstance(r, Exception) or r.get('status') == 'failed')

            # 5. 更新状态
            processing_time = int((datetime.now() - start_time).total_seconds())

            try:
                self.db.rollback()  # 先清理当前会话
            except:
                pass

            # 使用新会话更新最终状态
            from database import SessionFactory
            with SessionFactory() as fresh_db:
                fresh_record = fresh_db.query(ImportBatchRecords).filter(
                    ImportBatchRecords.id == batch_record.id
                ).first()
                if fresh_record:
                    fresh_record.processed_keywords = total_processed
                    fresh_record.total_records = total_processed
                    fresh_record.processing_seconds = processing_time

                    if failed_count == 0:
                        fresh_record.status = StatusEnum.COMPLETED
                        fresh_record.completed_at = datetime.now()
                        message = f"多进程处理完成: {total_processed} 条记录, {processing_time}秒"
                        success = True
                    else:
                        fresh_record.status = StatusEnum.FAILED
                        fresh_record.error_message = f"{failed_count} 个分片失败"
                        message = f"部分失败: 成功 {total_processed} 条, {failed_count} 个分片失败"
                        success = False

                    fresh_db.commit()

            return success, message, batch_record

        except Exception as e:
            logger.error(f"多进程处理失败: {e}")
            if batch_record:
                self._update_batch_record_error(batch_record, str(e))
            return False, str(e), batch_record

        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                await self._cleanup_temp_dir(temp_dir)

    async def _process_csv_with_upsert(
            self, file_path: str, batch_record: ImportBatchRecords, report_date: date, data_type: str
    ) -> Tuple[bool, str]:
        """单线程去重处理CSV文件"""
        try:
            processed_count = 0
            start_time = datetime.now()

            # 分块读取和处理
            chunk_count = 0
            for chunk_df in self.csv_processor.read_csv_chunks(file_path):
                chunk_processed = self.csv_processor.process_chunk_with_upsert(
                    chunk_df, report_date, data_type, self.db
                )

                processed_count += chunk_processed
                chunk_count += 1

                # 实时更新进度
                current_processing_seconds = int((datetime.now() - start_time).total_seconds())
                batch_record.processed_keywords = processed_count
                batch_record.processing_seconds = current_processing_seconds

                # 定期提交进度更新
                if chunk_count % 5 == 0:
                    try:
                        self.db.commit()
                    except Exception as e:
                        logger.warning(f"更新进度失败: {e}")

                # 记录详细进度
                if chunk_count % 10 == 0:
                    progress = (
                                           processed_count / batch_record.total_records) * 100 if batch_record.total_records > 0 else 0
                    logger.info(f"处理进度: {progress:.1f}% ({processed_count}条)")

            # 最终更新记录数
            batch_record.total_records = processed_count
            final_processing_time = int((datetime.now() - start_time).total_seconds())
            batch_record.processing_seconds = final_processing_time
            self.db.commit()

            logger.info(f"处理完成，总记录数: {processed_count}, 总耗时: {final_processing_time}秒")
            return True, f"处理成功 {processed_count} 条记录，耗时 {final_processing_time} 秒"

        except Exception as e:
            logger.error(f"处理失败: {e}")
            return False, f"处理失败: {str(e)}"

    async def _split_file_by_lines(self, file_path: str, temp_dir: str, lines_per_chunk: int) -> List[str]:
        """按行数 分片文件"""
        chunk_files = []

        with open(file_path, 'r', encoding='utf-8') as source:
            # 保存头部
            headers = [source.readline(), source.readline()]

            chunk_id = 0
            current_lines = 0
            chunk_file = None

            for line in source:
                # 创建新分片
                if chunk_file is None:
                    chunk_path = os.path.join(temp_dir, f"chunk_{chunk_id:03d}.csv")
                    chunk_file = open(chunk_path, 'w', encoding='utf-8')
                    chunk_file.writelines(headers)
                    chunk_files.append(chunk_path)
                    current_lines = 0

                chunk_file.write(line)
                current_lines += 1

                # 检查是否需要切换分片
                if current_lines >= lines_per_chunk:
                    chunk_file.close()
                    chunk_file = None
                    chunk_id += 1

            # 关闭最后一个文件
            if chunk_file:
                chunk_file.close()

        return chunk_files

    async def _monitor_progress(self, batch_record: ImportBatchRecords, start_time: datetime):
        """监控处理进度"""
        try:
            while True:
                await asyncio.sleep(10)

                # 检查批次记录是否还在处理中
                try:
                    from database import SessionFactory
                    with SessionFactory() as fresh_db:
                        fresh_record = fresh_db.query(ImportBatchRecords).filter(
                            ImportBatchRecords.id == batch_record.id
                        ).first()

                        if not fresh_record or fresh_record.status != StatusEnum.PROCESSING:
                            break

                        # 只更新处理时间，不执行其他可能返回结果的查询
                        processing_seconds = int((datetime.now() - start_time).total_seconds())
                        fresh_record.processing_seconds = processing_seconds
                        fresh_db.commit()

                except Exception as e:
                    logger.warning(f"更新进度失败: {e}")
                    # 简单的等待而不是复杂的重试逻辑
                    await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info("进度监控任务被取消")
        except Exception as e:
            logger.warning(f"进度监控异常: {e}")

    async def _cleanup_temp_dir(self, temp_dir: str):
        """清理临时目录"""
        try:
            import shutil
            shutil.rmtree(temp_dir)
            logger.info(f"清理临时目录: {temp_dir}")
        except Exception as e:
            logger.warning(f"清理临时目录失败: {e}")

    def _extract_date_from_filename(self, filename: str) -> Optional[date]:
        """从文件名中提取日期"""
        try:
            date_pattern = r'(\d{4})[_-](\d{2})[_-](\d{2})'
            match = re.search(date_pattern, filename)
            if match:
                year, month, day = match.groups()
                return date(int(year), int(month), int(day))
            logger.warning(f"无法从文件名 {filename} 中提取日期")
            return None
        except Exception as e:
            logger.error(f"解析文件名日期失败: {e}")
            return None

    def _create_batch_record(
            self, batch_name: str, import_date: date, total_records: int,
            is_day_data: bool, is_week_data: bool
    ) -> ImportBatchRecords:
        """创建导入批次记录"""
        try:
            batch_record = ImportBatchRecords(
                batch_name=batch_name,
                import_date=import_date,
                total_records=total_records,
                status=StatusEnum.PROCESSING,
                processed_keywords=0,
                processing_seconds=0,
                is_day_data=is_day_data,
                is_week_data=is_week_data,
                error_message="",
                created_at=datetime.now()
            )

            self.db.add(batch_record)
            self.db.commit()
            self.db.refresh(batch_record)

            logger.info(f"创建导入批次记录: {batch_record.id}")
            return batch_record

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建导入批次记录失败: {e}")
            raise

    def _update_batch_record_error(self, batch_record: ImportBatchRecords, error_message: str):
        """更新批次记录错误状态"""
        try:
            # 先回滚当前会话的问题
            try:
                self.db.rollback()
            except:
                pass

            # 使用新的数据库会话更新错误状态
            from database import SessionFactory
            with SessionFactory() as fresh_db:
                fresh_record = fresh_db.query(ImportBatchRecords).filter(
                    ImportBatchRecords.id == batch_record.id
                ).first()
                if fresh_record:
                    fresh_record.status = StatusEnum.FAILED
                    fresh_record.error_message = error_message[:500]  # 限制错误消息长度
                    fresh_record.completed_at = datetime.now()

                    if fresh_record.created_at:
                        fresh_record.processing_seconds = int(
                            (fresh_record.completed_at - fresh_record.created_at.replace(tzinfo=None)).total_seconds())

                    fresh_db.commit()
                    logger.info(f"已更新批次记录错误状态: {error_message[:100]}...")

        except Exception as e:
            logger.error(f"更新批次记录错误状态失败: {e}")