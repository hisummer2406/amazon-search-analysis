# app/services/optimized_upload_service.py - 简化版：单线程+多进程+去重
import asyncio
import logging
import os
import tempfile
from concurrent.futures import ProcessPoolExecutor
from typing import Tuple, Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from app.table.upload.processor.upload_service import UploadService
from app.table.upload.import_model import ImportBatchRecords, StatusEnum
from config import settings

logger = logging.getLogger(__name__)


def _process_chunk_worker(chunk_file: str, report_date_str: str, data_type: str, chunk_id: int) -> dict:
    """独立工作进程 - 处理单个分片文件"""
    try:
        from datetime import date
        from database import SessionFactory
        from app.table.upload.processor.csv_processor import CSVProcessor

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


class OptimizedUploadService(UploadService):
    """优化上传服务 - 智能选择处理策略"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.max_workers = min(settings.MAX_WORKERS, os.cpu_count())
        self.multiprocess_threshold = settings.MULTIPROCESSING_THRESHOLD_MB * 1024 * 1024  # 500MB阈值

    async def process_csv_file(
            self, file_path: str, original_filename: str, data_type: str
    ) -> Tuple[bool, str, Optional[ImportBatchRecords]]:
        """智能选择处理策略"""
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        if file_size >= self.multiprocess_threshold:
            logger.info(f"文件名：{original_filename}, 文件大小: {file_size_mb:.1f}MB, 多进程处理")
            # 大文件：多进程处理
            return await self._process_with_multiprocessing(file_path, original_filename, data_type)
        else:
            logger.info(f"文件名：{original_filename}, 文件大小: {file_size_mb:.1f}MB, 单线程处理")
            # 小文件：单线程去重处理
            return await super().process_csv_file(file_path, original_filename, data_type)

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
            logger.info(f"分片完成: {len(chunk_files)} 个文件")

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
            batch_record.processed_keywords = total_processed
            batch_record.total_records = total_processed
            batch_record.processing_seconds = processing_time

            if failed_count == 0:
                batch_record.status = StatusEnum.COMPLETED
                batch_record.completed_at = datetime.now()
                message = f"多进程处理完成: {total_processed} 条记录, {processing_time}秒"
                success = True
            else:
                batch_record.status = StatusEnum.FAILED
                batch_record.error_message = f"{failed_count} 个分片失败"
                message = f"部分失败: 成功 {total_processed} 条, {failed_count} 个分片失败"
                success = False

            self.db.commit()
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

    async def _split_file_by_lines(self, file_path: str, temp_dir: str, lines_per_chunk: int) -> List[str]:
        """按行数分片文件"""
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
            while batch_record.status == StatusEnum.PROCESSING:
                await asyncio.sleep(10)
                processing_seconds = int((datetime.now() - start_time).total_seconds())
                batch_record.processing_seconds = processing_seconds
                try:
                    self.db.commit()
                except:
                    pass
        except asyncio.CancelledError:
            pass
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
