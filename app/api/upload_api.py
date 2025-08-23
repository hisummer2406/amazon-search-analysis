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
from app.services.optimized_upload_service import OptimizedUploadService
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


async def process_csv_background_optimized(
        file_path: str,
        original_filename: str,
        data_type: str,
        db: Session
):
    """优化版后台处理CSV文件"""
    # 使用优化版服务
    upload_service = OptimizedUploadService(db)

    try:
        logger.info(f"开始优化处理文件: {original_filename}")

        success, message, batch_record = await upload_service.process_csv_file(
            file_path=file_path,
            original_filename=original_filename,
            data_type=data_type
        )

        if success:
            logger.info(f"优化处理成功: {original_filename} - {message}")
        else:
            logger.error(f"优化处理失败: {original_filename} - {message}")

    except Exception as e:
        logger.error(f"优化处理异常: {e}")
    finally:
        # 清理临时文件
        upload_service.cleanup_temp_file(file_path)


def validate_file(file: UploadFile) -> tuple[bool, str]:
    """验证上传文件"""
    # 检查是否有文件
    if not file or not file.filename:
        return False, "请选择要上传的文件"

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


def determine_data_type(filename: str, form_data_type: Optional[str] = None) -> str:
    """根据文件名和表单数据确定数据类型"""
    # 优先使用表单传递的数据类型
    if form_data_type and form_data_type in ['daily', 'weekly']:
        return form_data_type

    # 否则从文件名判断
    filename_lower = filename.lower()
    if 'day' in filename_lower:
        return 'daily'
    elif 'week' in filename_lower:
        return 'weekly'
    else:
        return 'daily'  # 默认返回daily


@upload_router.post("/upload-csv")
async def upload_csv_file(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(..., description="上传的CSV文件"),
        data_type: Optional[str] = Form(None, description="数据类型: daily 或 weekly"),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    try:
        logger.info(f"接收到文件上传请求: {file.filename if file else 'No file'}, data_type: {data_type}")

        # 验证文件
        is_valid, message = validate_file(file)
        if not is_valid:
            logger.warning(f"文件验证失败: {message}")
            return {
                "status": 1,
                "msg": message,
                "data": None
            }

        # 确定数据类型
        actual_data_type = determine_data_type(file.filename, data_type)
        logger.info(f"确定的数据类型: {actual_data_type}")

        if actual_data_type not in ['daily', 'weekly']:
            return {
                "status": 1,
                "msg": "数据类型必须是 'daily' 或 'weekly'",
                "data": None
            }

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"

        # 确定保存路径
        upload_dir = Path(settings.UPLOAD_DIR) / actual_data_type
        file_path = upload_dir / safe_filename

        logger.info(f"开始处理上传文件: {file.filename} -> {file_path}")

        # 保存文件
        success = await save_upload_file(file, str(file_path))
        if not success:
            return {
                "status": 1,
                "msg": "文件保存失败",
                "data": None
            }

        # 添加后台任务处理CSV
        background_tasks.add_task(
            # process_csv_background, 单线程
            process_csv_background_optimized,
            str(file_path),
            file.filename,
            actual_data_type,
            db
        )

        return {
            "status": 0,
            "msg": "文件上传成功，正在后台处理中...",
            "data": {
                "filename": file.filename,
                "data_type": actual_data_type,
                "file_size": getattr(file, 'size', 0),
                "upload_time": datetime.now().isoformat()
            }
        }

    except HTTPException as e:
        logger.error(f"HTTP异常: {e.detail}")
        return {
            "status": 1,
            "msg": e.detail,
            "data": None
        }
    except Exception as e:
        logger.error(f"上传文件失败: {e}")
        return {
            "status": 1,
            "msg": f"文件上传失败: {str(e)}",
            "data": None
        }


# 添加一个简单的测试端点来验证文件上传
@upload_router.post("/test-upload")
async def test_upload_file(
        file: UploadFile = File(..., description="测试上传文件"),
        test_param: str = Form("test", description="测试参数")
) -> Dict[str, Any]:
    """测试文件上传端点，用于调试"""
    try:
        logger.info(f"测试上传 - 文件名: {file.filename}, 参数: {test_param}")

        if not file or not file.filename:
            return {
                "status": 1,
                "msg": "没有接收到文件",
                "data": None
            }

        # 读取文件内容（仅用于测试，不保存）
        content = await file.read()

        return {
            "status": 0,
            "msg": "测试上传成功",
            "data": {
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(content),
                "test_param": test_param
            }
        }

    except Exception as e:
        logger.error(f"测试上传失败: {e}")
        return {
            "status": 1,
            "msg": f"测试上传失败: {str(e)}",
            "data": None
        }


@upload_router.get("/processing-status")
async def get_processing_status(
        db: Session = Depends(get_db())
) -> Dict[str, Any]:
    """获取正在处理中的任务状态"""
    try:
        from app.models.import_schemas import ImportBatchRecords, StatusEnum
        from sqlalchemy import desc

        # 查询正在处理中的记录
        processing_records = (db.query(ImportBatchRecords)
                              .order_by(desc(ImportBatchRecords.created_at))
                              .limit(5)
                              .all())

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
