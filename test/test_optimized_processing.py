import asyncio

from monitoring import PerformanceMonitor
from app.table.upload.processor.optimized_upload_service import OptimizedUploadService
import logging

logger = logging.getLogger(__name__)

async def test_optimized_processing():
    """测试优化处理性能"""
    from database import SessionFactory

    # 模拟不同大小的文件测试
    test_files = [
        ("small_file.csv", "daily", 50),  # 50MB
        ("medium_file.csv", "daily", 300),  # 300MB
        ("large_file.csv", "weekly", 2000),  # 2GB
    ]

    for filename, data_type, size_mb in test_files:
        logger.info(f"测试处理 {filename} ({size_mb}MB)")

        monitor = PerformanceMonitor()
        monitor.start()

        with SessionFactory() as db:
            service = OptimizedUploadService(db)

            # 这里需要实际的文件路径
            success, message, batch_record = await service.process_csv_file(
                file_path=f"/tmp/{filename}",
                original_filename=filename,
                data_type=data_type
            )

        performance_report = monitor.stop()
        logger.info(f"处理完成，性能报告: {performance_report}")


if __name__ == "__main__":
    # 运行性能测试
    asyncio.run(test_optimized_processing())