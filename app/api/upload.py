from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import os
import uuid
import asyncio
from datetime import datetime, date
import logging

from database import get_db, AsyncSessionFactory
from config import settings
from app.services.csv_processor import CSVProcessor
from app.services.batch_manager import BatchManager
from app.services.async_batch_processor import AsyncBatchProcessor
from app.schemas.import_batch import ImportBatchCreate, BatchStatus

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload-csv")
async def upload_csv_file(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        data_type: str = Form(..., description="数据类型: daily 或 weekly"),
        report_date: str = Form(..., description="报告日期 YYYY-MM-DD"),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """上传并处理CSV文件"""

    # 验证参数
    if data_type not in ['daily', 'weekly']:
        raise HTTPException(status_code=400, detail="数据类型必须是 'daily' 或 'weekly'")

    try:
        report_date_obj = datetime.strptime(report_date, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="报告日期格式错误，请使用 YYYY-MM-DD 格式")

    # 验证文件类型
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV文件")

    # 检查文件大小
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / (1024 * 1024 * 1024):.1f}GB)"
        )

    try:
        # 生成唯一文件名和路径
        file_id = str(uuid.uuid4())
        upload_subdir = f"{settings.UPLOAD_DIR}/{data_type}"
        file_path = os.path.join(upload_subdir, f"{file_id}_{file.filename}")

        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        logger.info(f"文件已保存: {file_path}")

        # 验证文件格式
        processor = CSVProcessor()
        is_valid, error_msg = processor.validate_csv_format(file_path)

        if not is_valid:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"CSV文件格式错误: {error_msg}")

        # 获取文件信息
        file_info = processor.estimate_file_info(file_path)

        # 创建批次记录
        batch_manager = BatchManager(db)
        batch_data = ImportBatchCreate(
            batch_name=file.filename,
            import_date=report_date_obj,
            day_data=(data_type == 'daily'),
            week_data=(data_type == 'weekly')
        )

        batch = batch_manager.create_batch(batch_data)

        # 启动后台处理任务
        background_tasks.add_task(
            process_csv_in_background,
            file_path=file_path,
            batch_id=batch.id,
            data_type=data_type,
            report_date=report_date_obj,
            file_info=file_info
        )

        logger.info(f"CSV文件上传成功，批次ID: {batch.id}")

        return {
            "message": "文件上传成功，正在后台处理",
            "batch_id": batch.id,
            "filename": file.filename,
            "data_type": data_type,
            "report_date": report_date,
            "estimated_records": file_info["estimated_rows"],
            "file_size_mb": file_info["file_size_mb"],
            "status": "processing"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传处理失败: {str(e)}")
        # 清理可能存在的临时文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")


@router.get("/batch-status/{batch_id}")
async def get_batch_status(batch_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """获取批次处理状态"""
    try:
        batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()

        if not batch:
            raise HTTPException(status_code=404, detail="批次不存在")

        return {
            "batch_id": batch.id,
            "batch_name": batch.batch_name,
            "status": batch.status,
            "import_date": batch.import_date.isoformat(),
            "total_records": batch.total_raw_records,
            "processed_records": batch.processed_keywords,
            "processing_time": batch.processing_time_seconds,
            "error_message": batch.error_message,
            "created_at": batch.created_at.isoformat(),
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "data_types": {
                "day_data": batch.day_data,
                "week_data": batch.week_data
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取批次状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取状态失败")


@router.get("/recent-batches")
async def get_recent_batches(
        days: int = 7,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取最近的批次列表"""
    try:
        batch_manager = BatchManager(db)
        batches = batch_manager.get_recent_batches(days)

        batch_list = []
        for batch in batches:
            batch_list.append({
                "id": batch.id,
                "batch_name": batch.batch_name,
                "import_date": batch.import_date.isoformat(),
                "status": batch.status,
                "total_records": batch.total_raw_records,
                "processed_records": batch.processed_keywords,
                "processing_time": batch.processing_time_seconds,
                "data_types": {
                    "day_data": batch.day_data,
                    "week_data": batch.week_data
                },
                "created_at": batch.created_at.isoformat(),
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None
            })

        return {
            "batches": batch_list,
            "total": len(batch_list),
            "days": days
        }

    except Exception as e:
        logger.error(f"获取最近批次失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取批次列表失败")


@router.post("/cleanup-old-data")
async def cleanup_old_data(
        keep_days: int = 30,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """清理旧数据"""
    try:
        # 使用异步处理器清理数据
        async with AsyncSessionLocal() as async_db:
            async_processor = AsyncBatchProcessor(async_db)
            deleted_count = await async_processor.cleanup_old_data(keep_days)

        return {
            "message": "数据清理完成",
            "deleted_records": deleted_count,
            "keep_days": keep_days
        }

    except Exception as e:
        logger.error(f"数据清理失败: {str(e)}")
        raise HTTPException(status_code=500, detail="数据清理失败")


@router.get("/batch-statistics")
async def get_batch_statistics(
        days: int = 30,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取批次统计信息"""
    try:
        batch_manager = BatchManager(db)
        stats = batch_manager.get_batch_statistics(days)

        return {
            "statistics": stats,
            "period_days": days
        }

    except Exception as e:
        logger.error(f"获取批次统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取统计失败")


async def process_csv_in_background(
        file_path: str,
        batch_id: int,
        data_type: str,
        report_date: date,
        file_info: Dict[str, Any]
):
    """后台处理CSV文件"""
    start_time = datetime.now()

    try:
        logger.info(f"开始后台处理批次 {batch_id}")

        # 获取数据库会话
        from app.database import SessionLocal
        from app.models.import_batch import ImportBatch

        sync_db = SessionLocal()

        try:
            # 更新批次状态为处理中
            batch_manager = BatchManager(sync_db)
            batch_manager.update_batch(batch_id, {
                "status": BatchStatus.PROCESSING,
                "total_raw_records": file_info["estimated_rows"]
            })

            # 处理CSV文件
            processor = CSVProcessor()
            total_records, processed_data = await processor.process_large_csv(
                file_path, data_type, report_date
            )

            logger.info(f"CSV解析完成，总记录数: {total_records}")

            # 使用异步处理器批量插入/更新数据
            async with AsyncSessionLocal() as async_db:
                async_processor = AsyncBatchProcessor(async_db)
                updated_count, inserted_count = await async_processor.upsert_search_data_batch(
                    processed_data, data_type
                )

            # 计算处理时间
            processing_time = int((datetime.now() - start_time).total_seconds())

            # 更新批次状态为完成
            batch_manager.update_batch(batch_id, {
                "status": BatchStatus.COMPLETED,
                "total_raw_records": total_records,
                "processed_keywords": updated_count + inserted_count,
                "processing_time_seconds": processing_time,
                "completed_at": datetime.now()
            })

            logger.info(f"批次 {batch_id} 处理完成，更新: {updated_count}, 插入: {inserted_count}")

        finally:
            sync_db.close()

    except Exception as e:
        logger.error(f"后台处理批次 {batch_id} 失败: {str(e)}")

        # 更新批次状态为失败
        try:
            from ..database import SessionLocal
            sync_db = SessionLocal()
            batch_manager = BatchManager(sync_db)
            processing_time = int((datetime.now() - start_time).total_seconds())

            batch_manager.update_batch(batch_id, {
                "status": BatchStatus.FAILED,
                "error_message": str(e),
                "processing_time_seconds": processing_time,
                "completed_at": datetime.now()
            })
            sync_db.close()
        except Exception as update_error:
            logger.error(f"更新失败状态时出错: {update_error}")

    finally:
        # 清理临时文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"临时文件已删除: {file_path}")
        except Exception as cleanup_error:
            logger.warning(f"清理临时文件失败: {cleanup_error}")