# app/api/upload_api.py - 修复版本
import logging
import os
import aiofiles
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from database import get_db, SessionFactory  # 导入SessionFactory
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
            while chunk := await upload_file.read(8192):  # 8KB小块
                await f.write(chunk)

        logger.info(f"文件保存成功: {file_path}")
        return True

    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        return False


def process_csv_background_optimized_sync(
        file_path: str,
        original_filename: str,
        data_type: str
):
    """
    同步版本的后台处理函数 - 独立数据库会话
    FastAPI的BackgroundTasks需要同步函数
    """
    # 创建独立的数据库会话，避免与API请求共享
    with SessionFactory() as independent_db:
        try:
            logger.info(f"开始独立会话处理文件: {original_filename}")

            # 使用独立的数据库会话创建服务
            upload_service = OptimizedUploadService(independent_db)

            # 由于BackgroundTasks期望同步函数，这里不使用async
            success, message, batch_record = _process_csv_sync(
                upload_service,
                file_path,
                original_filename,
                data_type
            )

            if success:
                logger.info(f"独立会话处理成功: {original_filename} - {message}")
            else:
                logger.error(f"独立会话处理失败: {original_filename} - {message}")

        except Exception as e:
            logger.error(f"独立会话处理异常: {e}")
        finally:
            # 清理临时文件
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.info(f"清理临时文件: {file_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")


def _process_csv_sync(
        upload_service: OptimizedUploadService,
        file_path: str,
        original_filename: str,
        data_type: str
):
    """同步处理CSV文件的内部函数"""
    import asyncio

    # 在新的事件循环中运行异步处理
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            upload_service.process_csv_file(
                file_path=file_path,
                original_filename=original_filename,
                data_type=data_type
            )
        )

        return result

    except Exception as e:
        logger.error(f"同步处理CSV异常: {e}")
        return False, str(e), None
    finally:
        try:
            loop.close()
        except:
            pass


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
        # db: Session = Depends(get_db)  # 仅用于验证和初始响应
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

        # 添加后台任务处理CSV - 使用独立数据库会话
        background_tasks.add_task(
            process_csv_background_optimized_sync,
            str(file_path),
            file.filename,
            actual_data_type
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
async def get_processing_status(data_type: str = None):
    with SessionFactory() as db:
        try:
            from app.models.import_schemas import ImportBatchRecords, StatusEnum
            from datetime import datetime
            from sqlalchemy import desc

            query = db.query(ImportBatchRecords)

            if data_type == 'daily':
                query = query.filter(ImportBatchRecords.is_day_data == True)
            if data_type == 'weekly':
                query = query.filter(ImportBatchRecords.is_week_data == True)

            records = query.order_by(desc(ImportBatchRecords.created_at)).limit(5).all()

            items = []
            for r in records:
                try:
                    # 修复时区问题：确保时间对象一致性
                    current_time = datetime.now()
                    created_time = r.created_at

                    # 如果created_at有时区信息，移除它
                    if hasattr(created_time, 'tzinfo') and created_time.tzinfo is not None:
                        created_time = created_time.replace(tzinfo=None)

                    if r.status.value == 'PROCESSING':
                        seconds = int((current_time - created_time).total_seconds())
                    else:
                        seconds = r.processing_seconds or 0

                except Exception as time_error:
                    # 如果时间计算失败，使用默认值
                    seconds = r.processing_seconds or 0

                items.append({
                    "batch_name": r.batch_name,
                    "status": "处理中" if r.status.value == 'PROCESSING' else r.status.value,
                    "progress_percent": round((r.processed_keywords / max(r.total_records, 1)) * 100, 1),
                    "processing_seconds": seconds,
                    "processed_keywords": r.processed_keywords,
                    "total_records": r.total_records
                })

            return {
                "status": 0,
                "msg": "success",
                "data": {"items": items}
            }

        except Exception as e:
            logger.error(f"获取处理状态失败: {e}")
            return {"status": 1, "msg": str(e), "data": {"items": []}}


def _get_status_display(status: 'StatusEnum') -> str:
    """获取状态显示文本"""
    status_map = {
        'PROCESSING': '处理中',
        'COMPLETED': '已完成',
        'FAILED': '失败'
    }
    return status_map.get(status.value, status.value)
