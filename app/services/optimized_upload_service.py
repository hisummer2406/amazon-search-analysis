import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, date
import os
from pathlib import Path

from sqlalchemy.orm import Session
from app.services.upload_service import UploadService
from app.models.import_schemas import ImportBatchRecords, StatusEnum
from app.services.csv_processor import CSVProcessor
from config import settings

logger = logging.getLogger(__name__)


class OptimizedUploadService(UploadService):
    """优化版上传服务 - 继承原有功能并添加多核处理"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.max_workers = min(4, os.cpu_count())
        self.use_multiprocessing_threshold = 1 * 1024 * 1024 * 1024  # 1GB
        logger.info(f"优化服务初始化，最大工作进程: {self.max_workers}")

    async def process_csv_file(
            self,
            file_path: str,
            original_filename: str,
            data_type: str
    ) -> Tuple[bool, str, Optional[ImportBatchRecords]]:
        """智能选择处理策略"""
        try:
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)

            logger.info(f"文件大小: {file_size_mb:.2f}MB，选择处理策略...")

            # 根据文件大小选择策略
            if file_size >= self.use_multiprocessing_threshold:
                # 大文件：多进程处理
                return await self._process_with_multiprocessing(
                    file_path, original_filename, data_type
                )
            elif file_size >= 100 * 1024 * 1024:  # 100MB
                # 中等文件：多线程处理
                return await self._process_with_multithreading(
                    file_path, original_filename, data_type
                )
            else:
                # 小文件：使用原有单线程处理
                return await super().process_csv_file(
                    file_path, original_filename, data_type
                )

        except Exception as e:
            logger.error(f"优化处理失败: {e}")
            return False, str(e), None

    async def _process_with_multiprocessing(
            self,
            file_path: str,
            original_filename: str,
            data_type: str
    ) -> Tuple[bool, str, Optional[ImportBatchRecords]]:
        """多进程处理大文件"""
        try:
            # 1. 文件预处理
            is_valid, validation_message = self.file_validator.validate_csv_structure(file_path)
            if not is_valid:
                return False, validation_message, None

            # 2. 提取报告日期
            report_date = self._extract_date_from_filename(original_filename)
            if not report_date:
                return False, "无法解析文件日期", None

            # 3. 文件分片
            chunk_files = await self._create_file_chunks(file_path, num_chunks=self.max_workers)

            # 4. 创建批次记录
            file_info = self.csv_processor.get_file_info(file_path)
            batch_record = self._create_batch_record(
                original_filename, report_date, file_info['estimated_records'],
                data_type == 'daily', data_type == 'weekly'
            )

            logger.info(f"开始多进程处理，分片数: {len(chunk_files)}")

            # 5. 并行处理分片
            loop = asyncio.get_event_loop()
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                tasks = []
                for i, chunk_file in enumerate(chunk_files):
                    task = loop.run_in_executor(
                        executor,
                        self._process_chunk_in_separate_process,
                        chunk_file,
                        report_date,
                        data_type,
                        i
                    )
                    tasks.append(task)

                # 等待所有任务完成
                results = await asyncio.gather(*tasks, return_exceptions=True)

            # 6. 处理结果
            total_processed = 0
            failed_chunks = 0

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"分片 {i} 处理失败: {result}")
                    failed_chunks += 1
                else:
                    total_processed += result['processed_count']
                    logger.info(f"分片 {i} 完成，处理 {result['processed_count']} 条记录")

            # 7. 更新批次记录
            if failed_chunks == 0:
                batch_record.status = StatusEnum.COMPLETED
                batch_record.processed_keywords = total_processed
                batch_record.total_records = total_processed
                message = f"多进程处理完成，总记录数: {total_processed}"
                success = True
            else:
                batch_record.status = StatusEnum.FAILED
                batch_record.error_message = f"有 {failed_chunks} 个分片处理失败"
                message = f"部分处理失败，成功处理 {total_processed} 条记录"
                success = False

            batch_record.completed_at = datetime.now()
            self.db.commit()

            # 8. 清理分片文件
            await self._cleanup_chunk_files(chunk_files)

            return success, message, batch_record

        except Exception as e:
            logger.error(f"多进程处理异常: {e}")
            return False, str(e), None

    async def _process_with_multithreading(
            self,
            file_path: str,
            original_filename: str,
            data_type: str
    ) -> Tuple[bool, str, Optional[ImportBatchRecords]]:
        """多线程处理中等大小文件"""
        try:
            # 验证和初始化
            is_valid, validation_message = self.file_validator.validate_csv_structure(file_path)
            if not is_valid:
                return False, validation_message, None

            report_date = self._extract_date_from_filename(original_filename)
            if not report_date:
                return False, "无法解析文件日期", None

            file_info = self.csv_processor.get_file_info(file_path)
            batch_record = self._create_batch_record(
                original_filename, report_date, file_info['estimated_records'],
                data_type == 'daily', data_type == 'weekly'
            )

            logger.info("开始多线程管道处理")

            # 创建数据队列
            data_queue = asyncio.Queue(maxsize=50)  # 限制队列大小

            # 创建任务
            reader_task = asyncio.create_task(
                self._data_reader_coroutine(file_path, report_date, data_type, data_queue)
            )

            writer_tasks = [
                asyncio.create_task(
                    self._data_writer_coroutine(f"writer_{i}", data_queue)
                )
                for i in range(2)  # 2个写入协程
            ]

            # 等待读取完成
            await reader_task

            # 发送停止信号
            for _ in writer_tasks:
                await data_queue.put(None)

            # 等待写入完成
            results = await asyncio.gather(*writer_tasks)

            # 统计结果
            total_processed = sum(r['processed_count'] for r in results)

            batch_record.status = StatusEnum.COMPLETED
            batch_record.processed_keywords = total_processed
            batch_record.total_records = total_processed
            batch_record.completed_at = datetime.now()
            self.db.commit()

            return True, f"多线程处理完成，总记录数: {total_processed}", batch_record

        except Exception as e:
            logger.error(f"多线程处理异常: {e}")
            return False, str(e), None

    def _process_chunk_in_separate_process(
            self,
            chunk_file: str,
            report_date: date,
            data_type: str,
            chunk_id: int
    ) -> Dict[str, Any]:
        """在独立进程中处理数据块"""
        try:
            # 每个进程创建独立的数据库连接
            from database import SessionFactory
            from app.models.analysis_schemas import AmazonOriginSearchData

            processor = CSVProcessor(batch_size=5000)
            processed_count = 0

            with SessionFactory() as db_session:
                for chunk_df in processor.read_csv_chunks(chunk_file):
                    records = processor.convert_chunk_to_records(
                        chunk_df, report_date, data_type
                    )

                    if records:
                        db_session.bulk_insert_mappings(AmazonOriginSearchData, records)
                        db_session.commit()
                        processed_count += len(records)

            # 清理分片文件
            os.unlink(chunk_file)

            logger.info(f"进程 {chunk_id} 完成，处理 {processed_count} 条记录")

            return {
                'chunk_id': chunk_id,
                'processed_count': processed_count,
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"进程 {chunk_id} 处理失败: {e}")
            return {
                'chunk_id': chunk_id,
                'processed_count': 0,
                'status': 'failed',
                'error': str(e)
            }

    async def _data_reader_coroutine(
            self,
            file_path: str,
            report_date: date,
            data_type: str,
            data_queue: asyncio.Queue
    ):
        """数据读取协程"""
        processor = CSVProcessor(batch_size=5000)
        loop = asyncio.get_event_loop()

        with ThreadPoolExecutor(max_workers=1) as executor:
            try:
                for chunk_df in processor.read_csv_chunks(file_path):
                    # 在线程中转换数据
                    records = await loop.run_in_executor(
                        executor,
                        processor.convert_chunk_to_records,
                        chunk_df,
                        report_date,
                        data_type
                    )

                    if records:
                        await data_queue.put(records)
                        logger.debug(f"读取并转换 {len(records)} 条记录")

            except Exception as e:
                logger.error(f"数据读取协程失败: {e}")
                await data_queue.put({'error': str(e)})

    async def _data_writer_coroutine(
            self,
            writer_name: str,
            data_queue: asyncio.Queue
    ) -> Dict[str, Any]:
        """数据写入协程"""
        from app.models.analysis_schemas import AmazonOriginSearchData

        processed_count = 0
        start_time = datetime.now()

        try:
            while True:
                data = await data_queue.get()

                if data is None:  # 停止信号
                    break

                if isinstance(data, dict) and 'error' in data:
                    logger.error(f"{writer_name} 收到错误: {data['error']}")
                    break

                # 写入数据库
                self.db.bulk_insert_mappings(AmazonOriginSearchData, data)
                self.db.commit()
                processed_count += len(data)

                logger.debug(f"{writer_name} 写入 {len(data)} 条记录")
                data_queue.task_done()

        except Exception as e:
            logger.error(f"{writer_name} 失败: {e}")

        processing_time = (datetime.now() - start_time).total_seconds()

        return {
            'writer_name': writer_name,
            'processed_count': processed_count,
            'processing_time': processing_time
        }

    async def _create_file_chunks(self, file_path: str, num_chunks: int = 4) -> List[str]:
        """将文件分割成指定数量的块"""
        file_size = os.path.getsize(file_path)
        chunk_size = file_size // num_chunks
        chunk_files = []

        logger.info(f"分割文件 {file_path}，目标分片数: {num_chunks}")

        with open(file_path, 'r', encoding='utf-8') as source:
            # 读取头部信息（前2行）
            header_lines = [source.readline(), source.readline()]

            current_pos = source.tell()

            for chunk_id in range(num_chunks):
                chunk_filename = f"{file_path}.chunk_{chunk_id}"

                # 计算这个分片应该读取的字节数
                if chunk_id == num_chunks - 1:
                    # 最后一个分片读取剩余所有内容
                    bytes_to_read = file_size - current_pos
                else:
                    bytes_to_read = chunk_size

                with open(chunk_filename, 'w', encoding='utf-8') as chunk_file:
                    # 写入头部
                    chunk_file.writelines(header_lines)

                    # 写入数据行
                    bytes_read = 0
                    while bytes_read < bytes_to_read:
                        line = source.readline()
                        if not line:  # 文件结束
                            break
                        chunk_file.write(line)
                        bytes_read += len(line.encode('utf-8'))

                    current_pos = source.tell()

                chunk_files.append(chunk_filename)
                logger.info(f"创建分片 {chunk_id}: {chunk_filename}")

        return chunk_files

    async def _cleanup_chunk_files(self, chunk_files: List[str]):
        """清理分片文件"""
        for chunk_file in chunk_files:
            try:
                if os.path.exists(chunk_file):
                    os.unlink(chunk_file)
                    logger.debug(f"清理分片文件: {chunk_file}")
            except Exception as e:
                logger.warning(f"清理分片文件失败 {chunk_file}: {e}")