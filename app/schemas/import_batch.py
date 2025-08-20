from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from enum import Enum


class BatchStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportBatchBase(BaseModel):
    batch_name: Optional[str] = Field(None, max_length=500, description="表格文件名")
    import_date: date = Field(..., description="报告日期")
    day_data: bool = Field(default=False, description="是否包含日数据")
    week_data: bool = Field(default=False, description="是否包含周数据")


class ImportBatchCreate(ImportBatchBase):
    pass


class ImportBatchUpdate(BaseModel):
    total_raw_records: Optional[int] = Field(None, description="总行数")
    processed_keywords: Optional[int] = Field(None, description="处理的关键词数")
    processing_time_seconds: Optional[int] = Field(None, description="处理时间(秒)")
    status: Optional[BatchStatus] = Field(None, description="处理状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class ImportBatch(ImportBatchBase):
    id: int
    total_raw_records: int
    processed_keywords: int
    processing_time_seconds: int
    status: BatchStatus
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ImportBatchSummary(BaseModel):
    """导入批次摘要"""
    id: int
    batch_name: str
    import_date: date
    status: BatchStatus
    total_records: int
    processed_records: int
    success_rate: float
    processing_time: int
    data_types: str  # "日数据", "周数据", "日+周数据"


class BatchStatistics(BaseModel):
    """批次统计信息"""
    total_batches: int
    successful_batches: int
    failed_batches: int
    processing_batches: int
    total_records_processed: int
    avg_processing_time: float
    recent_batches: list[ImportBatchSummary]