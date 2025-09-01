# app/services/upload_service.py - 去重更新版本
import logging
import re
from datetime import datetime, date
from pathlib import Path
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from app.table.upload.import_model import ImportBatchRecords, StatusEnum
from app.table.upload.processor.csv_processor import CSVProcessor
from app.table.upload.processor.csv_processor import FileValidator
from config import settings

logger = logging.getLogger(__name__)


class UploadService:
    """CSV文件上传处理服务 - 支持去重更新"""

    def __init__(self, db: Session):
        self.db = db
        self.batch_size = settings.BATCH_SIZE
        self.csv_processor = CSVProcessor(batch_size=self.batch_size)
        self.file_validator = FileValidator()

    async def process_csv_file(
        self,
        file_path: str,
        original_filename: str,
        data_type: str
    ) -> Tuple[bool, str, Optional[ImportBatchRecords]]:
        """处理CSV文件上传 - 去重更新版本"""
        batch_record = None
        try:
            # 1. 验证文件结构
            is_valid, validation_message = self.file_validator.validate_csv_structure(file_path)
            if not is_valid:
                return False, validation_message, None

            # 2. 解析文件名获取报告日期
            report_date = self._extract_date_from_filename(original_filename)
            if not report_date:
                return False, "无法从文件名中解析出日期", None

            # 3. 获取文件信息
            file_info = self.csv_processor.get_file_info(file_path)

            # 4. 创建导入批次记录
            batch_record = self._create_batch_record(
                batch_name=original_filename,
                import_date=report_date,
                total_records=file_info['estimated_records'],
                is_day_data=(data_type == 'daily'),
                is_week_data=(data_type == 'weekly')
            )

            logger.info(f"开始处理文件: {original_filename}, 预估记录数: {file_info['estimated_records']}")

            # 5. 使用去重逻辑处理CSV文件
            success, message = await self._process_csv_with_upsert(
                file_path, batch_record, report_date, data_type
            )

            if success:
                # 6. 更新批次记录为完成状态
                batch_record.status = StatusEnum.COMPLETED
                batch_record.completed_at = datetime.now()
                final_processing_seconds = int((batch_record.completed_at - batch_record.created_at).total_seconds())
                batch_record.processing_seconds = final_processing_seconds
                self.db.commit()
                logger.info(f"CSV文件处理完成: {original_filename}, 总耗时: {final_processing_seconds}秒")

            return success, message, batch_record

        except Exception as e:
            logger.error(f"处理CSV文件失败: {e}")
            if batch_record:
                self._update_batch_record_error(batch_record, str(e))
            return False, f"文件处理失败: {str(e)}", batch_record


    async def _process_csv_with_upsert(
        self,
        file_path: str,
        batch_record: ImportBatchRecords,
        report_date: date,
        data_type: str
    ) -> Tuple[bool, str]:
        """使用去重更新逻辑处理CSV文件"""
        try:
            processed_count = 0
            start_time = datetime.now()

            logger.info(f"开始去重处理文件: {file_path}")

            # 分块读取和处理
            chunk_count = 0
            for chunk_df in self.csv_processor.read_csv_chunks(file_path):
                chunk_start_time = datetime.now()

                # 使用去重更新逻辑处理数据块
                chunk_processed = self.csv_processor.process_chunk_with_upsert(
                    chunk_df, report_date, data_type, self.db
                )

                processed_count += chunk_processed
                chunk_count += 1

                # 实时更新进度
                current_time = datetime.now()
                current_processing_seconds = int((current_time - start_time).total_seconds())

                batch_record.processed_keywords = processed_count
                batch_record.processing_seconds = current_processing_seconds

                # 定期提交进度更新
                if chunk_count % 5 == 0:
                    try:
                        self.db.commit()
                        logger.debug(f"更新进度: {processed_count} 条记录")
                    except Exception as e:
                        logger.warning(f"更新进度失败: {e}")

                # 记录详细进度
                if chunk_count % 10 == 0:
                    progress = (processed_count / batch_record.total_records) * 100 if batch_record.total_records > 0 else 0
                    chunk_time = (datetime.now() - chunk_start_time).total_seconds()
                    logger.info(f"去重处理进度: {progress:.1f}% ({processed_count}条), 本批耗时: {chunk_time:.2f}秒")

            # 最终更新记录数
            batch_record.total_records = processed_count
            final_processing_time = int((datetime.now() - start_time).total_seconds())
            batch_record.processing_seconds = final_processing_time
            self.db.commit()

            logger.info(f"去重处理完成，总记录数: {processed_count}, 总耗时: {final_processing_time}秒")
            return True, f"去重处理成功 {processed_count} 条记录，耗时 {final_processing_time} 秒"

        except Exception as e:
            logger.error(f"去重处理失败: {e}")
            return False, f"去重处理失败: {str(e)}"

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
        self,
        batch_name: str,
        import_date: date,
        total_records: int,
        is_day_data: bool,
        is_week_data: bool
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
            batch_record.status = StatusEnum.FAILED
            batch_record.error_message = error_message
            batch_record.completed_at = datetime.now()

            if batch_record.created_at:
                batch_record.processing_seconds = int(
                    (batch_record.completed_at - batch_record.created_at).total_seconds())

            self.db.commit()
            logger.error(f"更新批次记录错误状态: {error_message}")
        except Exception as e:
            logger.error(f"更新批次记录错误状态失败: {e}")

    def cleanup_temp_file(self, file_path: str):
        """清理临时文件"""
        try:
            Path(file_path).unlink(missing_ok=True)
            logger.info(f"清理临时文件: {file_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")