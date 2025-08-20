import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, date
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import gc
from app.config import settings

logger = logging.getLogger(__name__)


class CSVProcessor:
    """大文件CSV处理服务"""

    def __init__(self):
        self.batch_size = settings.BATCH_SIZE
        self.max_workers = settings.MAX_WORKERS

        # CSV列映射
        self.column_mapping = {
            '搜索频率排名': 'current_rangking_day',
            '搜索词': 'keyword',
            '点击量最高的品牌 #1': 'top_brand',
            '点击量最高的类别 #1': 'top_category',
            '点击量最高的商品 #1：ASIN': 'top_product_asin',
            '点击量最高的商品 #1：商品名称': 'top_product_title',
            '点击量最高的商品 #1：点击份额': 'top_product_click_share',
            '点击量最高的商品 #1：转化份额': 'top_product_conversion_share',
            '报告日期': 'report_date_day'
        }

    async def process_large_csv(
            self,
            file_path: str,
            data_type: str,  # 'daily' or 'weekly'
            report_date: date
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """处理大型CSV文件"""
        try:
            logger.info(f"开始处理{data_type}数据文件: {file_path}")

            # 分块读取CSV
            chunk_iter = pd.read_csv(
                file_path,
                encoding='utf-8',
                chunksize=self.batch_size,
                low_memory=False,
                dtype=str  # 先全部按字符串读取，避免类型推断错误
            )

            total_records = 0
            processed_data = []

            # 使用线程池处理数据块
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                tasks = []

                for chunk_idx, chunk in enumerate(chunk_iter):
                    # 提交异步任务处理每个数据块
                    task = asyncio.get_event_loop().run_in_executor(
                        executor,
                        self._process_chunk,
                        chunk,
                        data_type,
                        report_date,
                        chunk_idx
                    )
                    tasks.append(task)

                    # 控制内存使用，每处理一定数量的块就等待完成
                    if len(tasks) >= self.max_workers:
                        chunk_results = await asyncio.gather(*tasks)
                        for chunk_data in chunk_results:
                            if chunk_data:
                                processed_data.extend(chunk_data)
                                total_records += len(chunk_data)
                        tasks = []

                        # 强制垃圾回收
                        gc.collect()

                # 处理剩余的任务
                if tasks:
                    chunk_results = await asyncio.gather(*tasks)
                    for chunk_data in chunk_results:
                        if chunk_data:
                            processed_data.extend(chunk_data)
                            total_records += len(chunk_data)

            logger.info(f"CSV处理完成，总记录数: {total_records}")
            return total_records, processed_data

        except Exception as e:
            logger.error(f"CSV处理失败: {str(e)}")
            raise

    def _process_chunk(
            self,
            chunk: pd.DataFrame,
            data_type: str,
            report_date: date,
            chunk_idx: int
    ) -> List[Dict[str, Any]]:
        """处理单个数据块"""
        try:
            logger.debug(f"处理数据块 {chunk_idx}，行数: {len(chunk)}")

            # 清理数据
            chunk = chunk.fillna('')
            chunk = chunk.replace([np.inf, -np.inf], 0)

            processed_records = []

            for _, row in chunk.iterrows():
                try:
                    # 基础数据验证
                    keyword = str(row.get('搜索词', '')).strip()
                    asin = str(row.get('点击量最高的商品 #1：ASIN', '')).strip()

                    if not keyword or not asin:
                        continue

                    # 构建记录
                    record = self._build_record(row, data_type, report_date)
                    if record:
                        processed_records.append(record)

                except Exception as e:
                    logger.warning(f"处理行数据失败: {e}")
                    continue

            logger.debug(f"数据块 {chunk_idx} 处理完成，有效记录: {len(processed_records)}")
            return processed_records

        except Exception as e:
            logger.error(f"处理数据块 {chunk_idx} 失败: {e}")
            return []

    def _build_record(self, row: pd.Series, data_type: str, report_date: date) -> Optional[Dict[str, Any]]:
        """构建单条记录"""
        try:
            # 基础字段
            record = {
                'keyword': str(row.get('搜索词', '')).strip(),
                'top_product_asin': str(row.get('点击量最高的商品 #1：ASIN', '')).strip(),
                'top_product_title': str(row.get('点击量最高的商品 #1：商品名称', '')).strip(),
                'top_brand': str(row.get('点击量最高的品牌 #1', '')).strip() or None,
                'top_category': str(row.get('点击量最高的类别 #1', '')).strip() or None,
            }

            # 数值字段处理
            try:
                record['top_product_click_share'] = float(row.get('点击量最高的商品 #1：点击份额', 0) or 0)
                record['top_product_conversion_share'] = float(row.get('点击量最高的商品 #1：转化份额', 0) or 0)
                ranking = int(row.get('搜索频率排名', 0) or 0)
            except (ValueError, TypeError):
                record['top_product_click_share'] = 0
                record['top_product_conversion_share'] = 0
                ranking = 0

            # 根据数据类型设置相应字段
            if data_type == 'daily':
                record.update({
                    'current_rangking_day': ranking,
                    'report_date_day': report_date,
                    'previous_rangking_day': ranking,  # 默认值，后续计算
                    'ranking_change_day': 0,
                    'ranking_trend_day': [],
                    'is_new_day': True,
                    # 周数据字段设置默认值
                    'current_rangking_week': ranking,
                    'report_date_week': report_date,
                    'previous_rangking_week': ranking,
                    'ranking_change_week': 0,
                    'is_new_week': False
                })
            else:  # weekly
                record.update({
                    'current_rangking_week': ranking,
                    'report_date_week': report_date,
                    'previous_rangking_week': ranking,  # 默认值，后续计算
                    'ranking_change_week': 0,
                    'is_new_week': True,
                    # 日数据字段设置默认值
                    'current_rangking_day': ranking,
                    'report_date_day': report_date,
                    'previous_rangking_day': ranking,
                    'ranking_change_day': 0,
                    'ranking_trend_day': [],
                    'is_new_day': False
                })

            return record

        except Exception as e:
            logger.warning(f"构建记录失败: {e}")
            return None

    def validate_csv_format(self, file_path: str) -> Tuple[bool, str]:
        """验证CSV文件格式"""
        try:
            # 读取前几行验证格式
            sample_df = pd.read_csv(file_path, encoding='utf-8', nrows=5)

            required_columns = ['搜索词', '搜索频率排名', '点击量最高的商品 #1：ASIN']
            missing_columns = []

            for col in required_columns:
                if col not in sample_df.columns:
                    missing_columns.append(col)

            if missing_columns:
                return False, f"缺少必要列: {', '.join(missing_columns)}"

            return True, "格式验证通过"

        except Exception as e:
            return False, f"文件格式验证失败: {str(e)}"

    def estimate_file_info(self, file_path: str) -> Dict[str, Any]:
        """估算文件信息"""
        try:
            import os
            file_size = os.path.getsize(file_path)

            # 读取一小部分估算总行数
            sample_chunk = pd.read_csv(file_path, encoding='utf-8', nrows=1000)
            sample_size = len(sample_chunk)

            # 粗略估算总行数（基于文件大小比例）
            estimated_rows = int((file_size / (file_size / 1000)) * sample_size) if sample_size > 0 else 0

            return {
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'estimated_rows': estimated_rows,
                'estimated_batches': max(1, estimated_rows // self.batch_size)
            }

        except Exception as e:
            logger.error(f"估算文件信息失败: {e}")
            return {
                'file_size_bytes': 0,
                'file_size_mb': 0,
                'estimated_rows': 0,
                'estimated_batches': 1
            }