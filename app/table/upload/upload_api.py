import logging
import os
import uuid
import aiofiles
import tempfile
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks

from app.table.upload.upload_schemas import ChunkStartRequest, FinishChunkRequest
from database import SessionFactory
from app.table.upload.upload_service import UploadService
from config import settings

logger = logging.getLogger(__name__)
upload_router = APIRouter()

# 分块上传状态管理
chunk_sessions: Dict[str, Dict[str, Any]] = {}
# 会话锁，防止并发修改
chunk_sessions_lock = asyncio.Lock()

# 会话超时时间（默认1小时）
CHUNK_SESSION_TIMEOUT = timedelta(hours=1)


async def process_csv_background_async(file_path: str, original_filename: str, data_type: str) -> None:
    """异步后台处理CSV文件 - 独立数据库会话，确保会话正确关闭"""
    db = None
    try:
        db = SessionFactory()
        upload_service = UploadService(db)
        success, message, batch_record = await upload_service.process_csv_file(
            file_path, original_filename, data_type
        )
        if success:
            logger.info(f"处理成功: {original_filename}, 批次: {batch_record.batch_name if batch_record else 'N/A'}")
        else:
            logger.error(f"处理失败: {message}")
    except Exception as e:
        logger.error(f"后台处理异常: {e}", exc_info=True)
    finally:
        # 确保数据库会话关闭
        if db is not None:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"关闭数据库会话失败: {e}")


def process_csv_background(file_path: str, original_filename: str, data_type: str) -> None:
    """同步包装器 - 在新的事件循环中运行异步函数"""
    try:
        asyncio.run(process_csv_background_async(file_path, original_filename, data_type))
    except Exception as e:
        logger.error(f"后台处理包装器异常: {e}", exc_info=True)
    finally:
        # 清理文件
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except Exception as cleanup_error:
                logger.error(f"清理文件失败: {cleanup_error}")


async def _cleanup_chunk_session(session_key: str) -> None:
    """清理分块上传会话"""
    async with chunk_sessions_lock:
        if session_key in chunk_sessions:
            session = chunk_sessions[session_key]
            try:
                import shutil
                if os.path.exists(session["temp_dir"]):
                    shutil.rmtree(session["temp_dir"])
                logger.info(f"已清理会话 {session_key} 的临时目录")
            except Exception as e:
                logger.warning(f"清理临时目录失败: {e}")
            finally:
                del chunk_sessions[session_key]
                logger.info(f"已删除会话: {session_key}")


async def _cleanup_expired_sessions() -> None:
    """清理过期的会话"""
    now = datetime.now()
    expired_keys = []
    async with chunk_sessions_lock:
        for key, session in chunk_sessions.items():
            created_at = session.get("created_at")
            if created_at and (now - created_at) > CHUNK_SESSION_TIMEOUT:
                expired_keys.append(key)

        for key in expired_keys:
            session = chunk_sessions[key]
            try:
                import shutil
                if os.path.exists(session["temp_dir"]):
                    shutil.rmtree(session["temp_dir"])
            except Exception as e:
                logger.warning(f"清理过期会话临时目录失败: {e}")
            finally:
                del chunk_sessions[key]
                logger.info(f"已清理过期会话: {key}")


@upload_router.post("/startChunkApi")
async def start_chunk_api(chunk: ChunkStartRequest) -> Dict[str, Any]:
    """
    AMIS分块上传 - 开始上传接口
    根据AMIS规范，需要返回包含key和uploadId的data对象
    """
    try:
        logger.info(f"收到AMIS分块上传请求 - filename: {chunk.filename}, data_type: {chunk.data_type}")

        # 生成唯一标识
        upload_id = str(uuid.uuid4())
        # AMIS要求的key格式，使用uuid确保唯一性
        key = f"{uuid.uuid4().hex}_{chunk.filename}"

        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="amis_chunk_")

        async with chunk_sessions_lock:
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
) -> Dict[str, Any]:
    """
    AMIS分块上传 - 上传分块接口
    AMIS会发送key和partNumber来标识每个分块
    """
    try:
        async with chunk_sessions_lock:
            session = chunk_sessions.get(key)
            if not session:
                logger.error(f"会话不存在: key={key}, partNumber={partNumber}, 当前所有会话keys={list(chunk_sessions.keys())}")
                return {"status": 1, "msg": "无效的上传会话key"}

        # 转换分块序号
        part_num = int(partNumber)
        logger.info(f"收到分块上传: key={key}, partNumber={part_num}, filename={file.filename}")

        # 保存分块文件（流式写入，避免大文件内存峰值）
        chunk_filename = f"part_{part_num:04d}.chunk"
        chunk_path = os.path.join(session["temp_dir"], chunk_filename)

        chunk_size = 0
        async with aiofiles.open(chunk_path, 'wb') as f:
            while upload_chunk := await file.read(65536):  # 64KB chunks
                await f.write(upload_chunk)
                chunk_size += len(upload_chunk)

        async with chunk_sessions_lock:
            # 重新获取会话，防止在写入期间被清理
            if key not in chunk_sessions:
                logger.error(f"会话在写入期间被清理: key={key}")
                return {"status": 1, "msg": "会话已失效"}

            # 记录分块信息
            chunk_sessions[key]["chunks"][part_num] = {
                "path": chunk_path,
                "size": chunk_size,
                "uploaded_at": datetime.now()
            }

        logger.info(f"分块 {part_num} 上传完成, key={key}, size={chunk_size}")

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
        logger.error(f"分块上传失败: key={key}, partNumber={partNumber}, error={e}", exc_info=True)
        return {"status": 1, "msg": str(e)}


def merge_chunks_and_process(
    session_key: str,
    session_data: Dict[str, Any],
    finish_chunk: FinishChunkRequest
) -> None:
    """后台任务：合并分块文件并处理CSV"""
    import shutil
    temp_dir = session_data.get("temp_dir")
    try:
        logger.info(f"开始后台合并分块文件: key={session_key}, 分块数量={len(session_data['chunks'])}")

        # 创建最终文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"{timestamp}_{session_data['filename']}"
        upload_dir = Path(settings.UPLOAD_DIR) / session_data["data_type"]
        upload_dir.mkdir(parents=True, exist_ok=True)
        final_path = upload_dir / final_filename

        # 按序号合并分块文件
        total_size = 0
        with open(final_path, 'wb') as outfile:
            sorted_parts = sorted(session_data["chunks"].items())
            for part_num, chunk_info in sorted_parts:
                chunk_path = chunk_info["path"]
                if os.path.exists(chunk_path):
                    with open(chunk_path, 'rb') as chunk_file:
                        chunk_data = chunk_file.read()
                        outfile.write(chunk_data)
                        total_size += len(chunk_data)
                else:
                    logger.error(f"分块文件不存在: {chunk_path}")
                    return

        logger.info(f"文件合并完成: {final_filename}, 总大小: {total_size / 1024 / 1024:.2f}MB")

        # 触发CSV处理
        process_csv_background(str(final_path), session_data['filename'], session_data['data_type'])

    except Exception as e:
        logger.error(f"后台合并处理失败: {e}", exc_info=True)
    finally:
        # 清理临时目录
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"已清理临时目录: {temp_dir}")
        except Exception as e:
            logger.warning(f"清理临时目录失败: {e}")


@upload_router.post("/finishChunkApi")
async def finish_chunk_api(
    background_tasks: BackgroundTasks,
    finish_chunk: FinishChunkRequest,
) -> Dict[str, Any]:
    """
    AMIS分块上传 - 完成上传接口
    立即返回响应，文件合并在后台任务中执行（避免504超时）
    """
    session_copy = None
    try:
        async with chunk_sessions_lock:
            if finish_chunk.key not in chunk_sessions:
                logger.error(f"finishChunkApi: 会话不存在, key={finish_chunk.key}")
                return {"status": 1, "msg": "无效的上传会话key"}

            session = chunk_sessions[finish_chunk.key]

            # 验证分块完整性
            expected_chunks = len(session["chunks"])
            if expected_chunks == 0:
                logger.error(f"finishChunkApi: 没有接收到任何分块, key={finish_chunk.key}")
                return {"status": 1, "msg": "没有接收到任何分块"}

            logger.info(f"接收完成上传请求: key={finish_chunk.key}, 分块数量={expected_chunks}")

            # 复制会话数据并立即删除会话，防止后续分块请求继续进来
            session_copy = session.copy()
            del chunk_sessions[finish_chunk.key]
            logger.info(f"已从会话字典中删除: {finish_chunk.key}")

        # 立即添加后台任务进行文件合并和处理
        background_tasks.add_task(
            merge_chunks_and_process,
            finish_chunk.key,
            session_copy,
            finish_chunk
        )

        # 立即返回，不等待文件合并完成
        return {
            "status": 0,
            "msg": "文件上传成功，正在后台合并和处理",
            "data": {
                "filename": session_copy['filename'],
                "data_type": session_copy['data_type'],
                "chunks_count": expected_chunks,
                "status": "pending_merge"
            }
        }

    except Exception as e:
        logger.error(f"完成分块上传失败: key={finish_chunk.key}, error={e}", exc_info=True)
        # 如果出错，尝试清理会话
        if finish_chunk.key in chunk_sessions:
            await _cleanup_chunk_session(finish_chunk.key)
        return {"status": 1, "msg": f"服务器错误: {str(e)}"}


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
async def get_processing_status(data_type: Optional[str] = None) -> Dict[str, Any]:
    """获取处理状态"""
    with SessionFactory() as db:
        try:
            from app.table.upload.import_model import ImportBatchRecords
            from sqlalchemy import desc, select

            stmt = select(ImportBatchRecords)
            if data_type == 'daily':
                stmt = stmt.where(ImportBatchRecords.is_day_data == True)
            elif data_type == 'weekly':
                stmt = stmt.where(ImportBatchRecords.is_week_data == True)

            stmt = stmt.order_by(desc(ImportBatchRecords.created_at)).limit(5)
            records = list(db.execute(stmt).scalars().all())

            items = []
            for r in records:
                progress = round((r.processed_keywords / max(r.total_records, 1)) * 100, 1)
                items.append({
                    "batch_name": r.batch_name,
                    "progress_percent": progress,
                    "total_records": r.total_records,
                    "status": "处理中" if r.status.value == 'PROCESSING' else r.status.value
                })

            return {
                "status": 0,
                "data": {
                    "items": items,
                    "active_sessions": len(chunk_sessions)
                }
            }

        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return {"status": 1, "data": {"items": []}}


@upload_router.get("/concurrent-status")
async def get_concurrent_status() -> Dict[str, Any]:
    """获取上传会话状态"""
    return {
        "status": 0,
        "data": {
            "active_chunk_sessions": len(chunk_sessions),
            "chunk_session_keys": list(chunk_sessions.keys())[:10]  # 只返回前10个key用于调试
        }
    }