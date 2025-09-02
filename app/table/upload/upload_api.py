# app/api/upload_api.py - 修复异步调用问题
import logging
import os
import uuid
import aiofiles
import tempfile
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from app.table.upload.upload_schemas import ChunkStartRequest, FinishChunkRequest
from database import SessionFactory
from app.table.upload.processor.optimized_upload_service import OptimizedUploadService
from config import settings

logger = logging.getLogger(__name__)
upload_router = APIRouter()

# 分块上传状态管理
chunk_sessions = {}


async def process_csv_background_async(file_path: str, original_filename: str, data_type: str):
    """异步后台处理CSV文件 - 独立数据库会话"""
    with SessionFactory() as db:
        try:
            upload_service = OptimizedUploadService(db)
            success, message, batch_record = await upload_service.process_csv_file(
                file_path, original_filename, data_type
            )
            if success:
                logger.info(f"处理成功: {original_filename}")
            else:
                logger.error(f"处理失败: {message}")
        except Exception as e:
            logger.error(f"后台处理异常: {e}")
        finally:
            # 清理文件
            if os.path.exists(file_path):
                os.unlink(file_path)


def process_csv_background(file_path: str, original_filename: str, data_type: str):
    """同步包装器 - 在新的事件循环中运行异步函数"""
    try:
        # 创建新的事件循环来运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                process_csv_background_async(file_path, original_filename, data_type)
            )
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"后台处理包装器异常: {e}")
        # 确保清理文件
        if os.path.exists(file_path):
            os.unlink(file_path)


async def _cleanup_chunk_session(session_key: str):
    """清理分块上传会话"""
    if session_key in chunk_sessions:
        session = chunk_sessions[session_key]
        try:
            import shutil
            if os.path.exists(session["temp_dir"]):
                shutil.rmtree(session["temp_dir"])
        except Exception as e:
            logger.warning(f"清理临时目录失败: {e}")
        finally:
            del chunk_sessions[session_key]


@upload_router.post("/startChunkApi")
async def start_chunk_api(
        chunk: ChunkStartRequest,
):
    """
    AMIS分块上传 - 开始上传接口
    根据AMIS规范，需要返回包含key和uploadId的data对象
    """
    try:
        logger.info(f"收到AMIS分块上传请求 - filename: {chunk.filename}, data_type: {chunk.data_type}")

        # 生成唯一标识
        upload_id = str(uuid.uuid4())
        # AMIS要求的key格式，通常包含时间戳和文件名
        key = f"{int(datetime.now().timestamp())}_{chunk.filename}"

        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="amis_chunk_")

        # 保存会话信息
        chunk_sessions[key] = {
            "upload_id": upload_id,
            "filename": chunk.filename,
            "data_type": chunk.data_type,
            "temp_dir": temp_dir,
            "chunks": {},  # 存储分块信息 {partNumber: chunk_path}
            "created_at": datetime.now()
        }

        logger.info(f"AMIS分块上传会话创建: key={key}, upload_id={upload_id}")

        # 返回AMIS期望的格式
        return {
            "status": 0,
            "data": {
                "key": key,
                "uploadId": upload_id,
                "date": datetime.now().isoformat()
            },
            "msg": "分块上传会话创建成功"
        }

    except Exception as e:
        logger.error(f"开始分块上传失败: {e}")
        return {"status": 1, "msg": f"服务器错误: {str(e)}"}


@upload_router.post("/chunkApi")
async def chunk_api(
        key: str = Form(..., description="上传会话key"),
        partNumber: str = Form(..., description="分块序号"),
        file: UploadFile = File(..., description="分块文件")
):
    """
    AMIS分块上传 - 上传分块接口
    AMIS会发送key和partNumber来标识每个分块
    """
    try:
        if key not in chunk_sessions:
            return {"status": 1, "msg": "无效的上传会话key"}

        # 转换分块序号
        part_num = int(partNumber)
        session = chunk_sessions[key]

        # 保存分块文件
        chunk_filename = f"part_{part_num:04d}.chunk"
        chunk_path = os.path.join(session["temp_dir"], chunk_filename)

        async with aiofiles.open(chunk_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # 记录分块信息
        session["chunks"][part_num] = {
            "path": chunk_path,
            "size": len(content),
            "uploaded_at": datetime.now()
        }

        logger.debug(f"分块 {part_num} 上传完成, key={key}")

        return {
            "status": 0,
            "msg": "分块上传成功",
            "data": {
                "partNumber": part_num,
                "key": key
            }
        }

    except ValueError:
        logger.error(f"分块序号参数错误: {partNumber}")
        return {"status": 1, "msg": "分块序号参数无效"}
    except Exception as e:
        logger.error(f"分块上传失败: {e}")
        return {"status": 1, "msg": str(e)}


@upload_router.post("/finishChunkApi")
async def finish_chunk_api(
        background_tasks: BackgroundTasks,
        finish_chunk: FinishChunkRequest,
):
    """
    AMIS分块上传 - 完成上传接口
    合并所有分块并开始后台处理
    """
    try:
        if finish_chunk.key not in chunk_sessions:
            return {"status": 1, "msg": "无效的上传会话key"}

        session = chunk_sessions[finish_chunk.key]
        logger.info(f"开始合并分块文件: key={finish_chunk.key}, 分块数量={len(session['chunks'])}")

        # 创建最终文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"{timestamp}_{session['filename']}"
        upload_dir = Path(settings.UPLOAD_DIR) / session["data_type"]
        upload_dir.mkdir(parents=True, exist_ok=True)
        final_path = upload_dir / final_filename

        # 按序号合并分块文件
        total_size = 0
        with open(final_path, 'wb') as outfile:
            # 按分块序号排序
            sorted_parts = sorted(session["chunks"].items())
            for part_num, chunk_info in sorted_parts:
                chunk_path = chunk_info["path"]
                if os.path.exists(chunk_path):
                    with open(chunk_path, 'rb') as chunk_file:
                        chunk_data = chunk_file.read()
                        outfile.write(chunk_data)
                        total_size += len(chunk_data)
                else:
                    logger.error(f"分块文件不存在: {chunk_path}")
                    await _cleanup_chunk_session(finish_chunk.key)
                    return {"status": 1, "msg": f"分块文件缺失: part {part_num}"}

        logger.info(f"文件合并完成: {final_filename}, 总大小: {total_size / 1024 / 1024:.2f}MB")

        # 添加后台处理任务
        background_tasks.add_task(
            process_csv_background,
            str(final_path),
            session['filename'],
            session['data_type']
        )

        # 清理分块会话
        await _cleanup_chunk_session(finish_chunk.key)

        return {
            "status": 0,
            "msg": "文件上传成功，正在后台处理",
            "data": {
                "filename": session['filename'],
                "data_type": session['data_type'],
                "filesize": total_size,
                "final_path": str(final_path)
            }
        }

    except Exception as e:
        logger.error(f"完成分块上传失败: {e}")
        if finish_chunk.key in chunk_sessions:
            await _cleanup_chunk_session(finish_chunk.key)
        return {"status": 1, "msg": str(e)}


# 保持原有的传统上传接口和状态查询接口不变
@upload_router.post("/upload-csv")
async def upload_csv_file(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        data_type: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """传统上传方式 - 兼容小文件"""
    try:
        if not file or not file.filename:
            return {"status": 1, "msg": "请选择要上传的文件"}

        if not file.filename.lower().endswith('.csv'):
            return {"status": 1, "msg": "只支持CSV文件"}

        # 确定数据类型
        data_type = data_type or ('daily' if 'day' in file.filename.lower() else 'weekly')

        # 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        upload_dir = Path(settings.UPLOAD_DIR) / data_type
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / safe_filename

        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):
                await f.write(chunk)

        # 后台处理
        background_tasks.add_task(
            process_csv_background,
            str(file_path),
            file.filename,
            data_type
        )

        return {
            "status": 0,
            "msg": "文件上传成功，正在后台处理",
            "data": {
                "filename": file.filename,
                "data_type": data_type
            }
        }

    except Exception as e:
        logger.error(f"上传失败: {e}")
        return {"status": 1, "msg": str(e)}


@upload_router.get("/processing-status")
async def get_processing_status(data_type: str = None):
    """获取处理状态"""
    with SessionFactory() as db:
        try:
            from app.table.upload.import_model import ImportBatchRecords
            from sqlalchemy import desc

            query = db.query(ImportBatchRecords)
            if data_type == 'daily':
                query = query.filter(ImportBatchRecords.is_day_data == True)
            elif data_type == 'weekly':
                query = query.filter(ImportBatchRecords.is_week_data == True)

            records = query.order_by(desc(ImportBatchRecords.created_at)).limit(5).all()

            items = []
            for r in records:
                progress = round((r.processed_keywords / max(r.total_records, 1)) * 100, 1)
                items.append({
                    "batch_name": r.batch_name,
                    "progress_percent": progress,
                    "total_records": r.total_records,
                    "status": "处理中" if r.status.value == 'PROCESSING' else r.status.value
                })

            return {"status": 0, "data": {"items": items}}

        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return {"status": 1, "data": {"items": []}}