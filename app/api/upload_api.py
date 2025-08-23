import logging
import os
import aiofiles
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from database import get_db
from app.services.upload_service import UploadService
from config import settings

logger = logging.getLogger(__name__)
upload_router = APIRouter()


async def save_upload_file(upload_file: UploadFile, file_path: str) -> bool:
    """异步保存上传文件"""
    try:
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, 'wb') as f:
            content = await upload_file.read()
            await f.write(content)

        logger.info(f"文件保存成功: {file_path}")
        return True

    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        return False


async def process_csv_background(
        file_path: str,
        original_filename: str,
        data_type: str,
        db: Session
):
    """后台处理CSV文件"""
    upload_service = UploadService(db)

    try:
        logger.info(f"开始后台处理文件: {original_filename}")

        # 处理CSV文件
        success, message, batch_record = await upload_service.process_csv_file(
            file_path=file_path,
            original_filename=original_filename,
            data_type=data_type
        )

        if success:
            logger.info(f"文件处理成功: {original_filename} - {message}")
        else:
            logger.error(f"文件处理失败: {original_filename} - {message}")

    except Exception as e:
        logger.error(f"后台处理文件异常: {e}")
    finally:
        # 清理临时文件
        upload_service.cleanup_temp_file(file_path)


def validate_file(file: UploadFile) -> tuple[bool, str]:
    """验证上传文件"""
    # 检查文件类型
    if not file.filename.lower().endswith('.csv'):
        return False, "只支持CSV文件格式"

    # 检查文件名格式 (应该包含Day或Week以及日期)
    filename = file.filename.lower()
    if 'day' not in filename and 'week' not in filename:
        return False, "文件名必须包含'Day'或'Week'标识"

    # 检查文件大小
    if hasattr(file, 'size') and file.size:
        if file.size > settings.MAX_FILE_SIZE:
            size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"文件大小超过限制({size_mb:.0f}MB)"

    return True, "文件验证通过"


def determine_data_type(filename: str) -> str:
    """根据文件名确定数据类型"""
    filename_lower = filename.lower()
    if 'day' in filename_lower:
        return 'daily'
    elif 'week' in filename_lower:
        return 'weekly'
    else:
        return 'daily'  # 默认返回daily


@upload_router.post("/file")
async def upload_csv_file(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        data_type: Optional[str] = Form(None, description="数据类型: daily 或 weekly"),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    上传CSV文件并异步处理

    Args:
        file: 上传的CSV文件
        data_type: 数据类型 ('daily' 或 'weekly')，如果未提供则从文件名自动判断
        db: 数据库会话

    Returns:
        上传结果
    """
    try:
        # 验证文件
        is_valid, message = validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)

        # 确定数据类型
        if not data_type:
            data_type = determine_data_type(file.filename)

        if data_type not in ['daily', 'weekly']:
            raise HTTPException(
                status_code=400,
                detail="数据类型必须是 'daily' 或 'weekly'"
            )

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"

        # 确定保存路径
        upload_dir = Path(settings.UPLOAD_DIR) / data_type
        file_path = upload_dir / safe_filename

        logger.info(f"开始处理上传文件: {file.filename} -> {file_path}")

        # 保存文件
        success = await save_upload_file(file, str(file_path))
        if not success:
            raise HTTPException(status_code=500, detail="文件保存失败")

        # 添加后台任务处理CSV
        background_tasks.add_task(
            process_csv_background,
            str(file_path),
            file.filename,
            data_type,
            db
        )

        return {
            "status": 0,
            "msg": "文件上传成功，正在后台处理中...",
            "data": {
                "filename": file.filename,
                "data_type": data_type,
                "file_size": getattr(file, 'size', 0),
                "upload_time": datetime.now().isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文件失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )


@upload_router.get("/processing-status")
async def get_processing_status(
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取正在处理中的任务状态"""
    try:
        from app.models.import_schemas import ImportBatchRecords, StatusEnum
        from sqlalchemy import desc

        # 查询正在处理中的记录
        processing_records = db.query(ImportBatchRecords).filter(
            ImportBatchRecords.status == StatusEnum.PROCESSING
        ).order_by(desc(ImportBatchRecords.created_at)).limit(10).all()

        # 格式化数据
        items = []
        for record in processing_records:
            progress = 0
            if record.total_records > 0:
                progress = (record.processed_keywords / record.total_records) * 100

            items.append({
                "id": record.id,
                "batch_name": record.batch_name,
                "status": record.status.value,
                "total_records": record.total_records,
                "processed_keywords": record.processed_keywords,
                "progress_percent": round(progress, 2),
                "processing_seconds": record.processing_seconds,
                "is_day_data": record.is_day_data,
                "is_week_data": record.is_week_data,
                "created_at": record.created_at.isoformat()
            })

        return {
            "status": 0,
            "msg": "获取成功",
            "data": {
                "items": items,
                "count": len(items)
            }
        }

    except Exception as e:
        logger.error(f"获取处理状态失败: {e}")
        return {
            "status": 1,
            "msg": f"获取状态失败: {str(e)}",
            "data": {
                "items": [],
                "count": 0
            }
        }


@upload_router.get("/recent-completed")
async def get_recent_completed(
        limit: int = 5,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取最近完成的任务"""
    try:
        from app.models.import_schemas import ImportBatchRecords, StatusEnum
        from sqlalchemy import desc

        # 查询最近完成的记录
        completed_records = db.query(ImportBatchRecords).filter(
            ImportBatchRecords.status.in_([StatusEnum.COMPLETED, StatusEnum.FAILED])
        ).order_by(desc(ImportBatchRecords.completed_at)).limit(limit).all()

        # 格式化数据
        items = []
        for record in completed_records:
            items.append({
                "id": record.id,
                "batch_name": record.batch_name,
                "status": record.status.value,
                "total_records": record.total_records,
                "processed_keywords": record.processed_keywords,
                "processing_seconds": record.processing_seconds,
                "is_day_data": record.is_day_data,
                "is_week_data": record.is_week_data,
                "error_message": record.error_message,
                "created_at": record.created_at.isoformat(),
                "completed_at": record.completed_at.isoformat() if record.completed_at else None
            })

        return {
            "status": 0,
            "msg": "获取成功",
            "data": {
                "items": items,
                "count": len(items)
            }
        }

    except Exception as e:
        logger.error(f"获取完成记录失败: {e}")
        return {
            "status": 1,
            "msg": f"获取记录失败: {str(e)}",
            "data": {
                "items": [],
                "count": 0
            }
        }