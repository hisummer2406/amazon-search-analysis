import logging
import pandas as pd
from typing import Iterator, Dict, Any, List, Optional
from pathlib import Path
import csv
from datetime import datetime, date

logger = logging.getLogger(__name__)


class CSVProcessor:
    """CSV文件处理工具类 - 专为大文件优化"""

    def __init__(self, batch_size: int = 10000):
        self.batch_size = batch_size

    def read_csv_chunks(self, file_path: str) -> Iterator[pd.DataFrame]:
        """分块读取大CSV文件"""
        try:
            # 先读取表头信息
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if len(lines) < 3:
                raise ValueError("CSV文件格式不正确，行数不足")

            # 获取表头行（第2行）
            header_line = lines[1].strip()
            headers = [h.strip() for h in header_line.split(',')]

            # 创建列名映射
            column_mapping = self._create_column_mapping(len(headers))
            temp_column_names = [f'col_{i}' for i in range(len(headers))]

            # 分块读取数据
            chunk_reader = pd.read_csv(
                file_path,
                skiprows=2,
                header=None,
                names=temp_column_names,
                dtype=str,
                encoding='utf-8',
                chunksize=self.batch_size,
                on_bad_lines='skip'
            )

            for chunk_df in chunk_reader:
                # 重命名列
                chunk_df = chunk_df.rename(columns=column_mapping)
                # 清理数据
                chunk_df = self._clean_chunk_data(chunk_df)
                # 过滤空行
                chunk_df = chunk_df.dropna(subset=['keyword']).reset_index(drop=True)

                if len(chunk_df) > 0:
                    yield chunk_df

        except Exception as e:
            logger.error(f"分块读取CSV文件失败: {e}")
            raise

    def _create_column_mapping(self, header_count: int) -> Dict[str, str]:
        """创建列名映射"""
        standard_columns = [
            'current_rangking_day',  # 搜索频率排名
            'keyword',  # 搜索词
            'top_brand',  # 品牌 #1
            'brand_2nd',  # 品牌 #2
            'brand_3rd',  # 品牌 #3
            'top_category',  # 类别 #1
            'category_2nd',  # 类别 #2
            'category_3rd',  # 类别 #3
            'top_product_asin',  # 商品 #1 ASIN
            'top_product_title',  # 商品 #1 标题
            'top_product_click_share',  # 商品 #1 点击份额
            'top_product_conversion_share',  # 商品 #1 转化份额
            'product_asin_2nd',  # 商品 #2 ASIN
            'product_title_2nd',  # 商品 #2 标题
            'product_click_share_2nd',  # 商品 #2 点击份额
            'product_conversion_share_2nd',  # 商品 #2 转化份额
            'product_asin_3rd',  # 商品 #3 ASIN
            'product_title_3rd',  # 商品 #3 标题
            'product_click_share_3rd',  # 商品 #3 点击份额
            'product_conversion_share_3rd',  # 商品 #3 转化份额
            'report_date'  # 报告日期
        ]

        mapping = {}
        for i in range(min(len(standard_columns), header_count)):
            mapping[f'col_{i}'] = standard_columns[i]

        return mapping

    def _clean_chunk_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清理数据块"""
        try:
            # 填充空值
            df = df.fillna('')

            # 数值列转换
            numeric_columns = [
                'current_rangking_day', 'top_product_click_share', 'top_product_conversion_share',
                'product_click_share_2nd', 'product_conversion_share_2nd',
                'product_click_share_3rd', 'product_conversion_share_3rd'
            ]

            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # 字符串列清理
            string_columns = [
                'keyword', 'top_brand', 'brand_2nd', 'brand_3rd',
                'top_category', 'category_2nd', 'category_3rd',
                'top_product_asin', 'product_asin_2nd', 'product_asin_3rd',
                'top_product_title', 'product_title_2nd', 'product_title_3rd'
            ]

            for col in string_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()

            return df

        except Exception as e:
            logger.error(f"清理数据块失败: {e}")
            raise

    def convert_chunk_to_records(
            self,
            df: pd.DataFrame,
            report_date: date,
            data_type: str
    ) -> List[Dict[str, Any]]:
        """将数据块转换为数据库记录"""
        records = []
        current_time = datetime.now()

        for _, row in df.iterrows():
            try:
                # 安全地获取数值，避免NaN
                def safe_get(col, default=0, dtype=None):
                    val = row.get(col, default)
                    if pd.isna(val):
                        return default
                    if dtype == int:
                        return int(float(val)) if val != '' else default
                    elif dtype == float:
                        return float(val) if val != '' else default
                    else:
                        return str(val).strip() if val != '' else str(default)

                record = {
                    'keyword': safe_get('keyword', ''),

                    # 排名字段
                    'current_rangking_day': safe_get('current_rangking_day', 0, int),
                    'report_date_day': report_date if data_type == 'daily' else report_date,
                    'previous_rangking_day': 0,
                    'ranking_change_day': 0,
                    'ranking_trend_day': [],

                    'current_rangking_week': safe_get('current_rangking_day', 0, int) if data_type == 'weekly' else 0,
                    'report_date_week': report_date if data_type == 'weekly' else report_date,
                    'previous_rangking_week': 0,
                    'ranking_change_week': 0,

                    # Top产品信息
                    'top_brand': safe_get('top_brand', ''),
                    'top_category': safe_get('top_category', ''),
                    'top_product_asin': safe_get('top_product_asin', ''),
                    'top_product_title': safe_get('top_product_title', ''),
                    'top_product_click_share': safe_get('top_product_click_share', 0.0, float),
                    'top_product_conversion_share': safe_get('top_product_conversion_share', 0.0, float),

                    # 第二名产品信息
                    'brand_2nd': safe_get('brand_2nd', ''),
                    'category_2nd': safe_get('category_2nd', ''),
                    'product_asin_2nd': safe_get('product_asin_2nd', ''),
                    'product_title_2nd': safe_get('product_title_2nd', ''),
                    'product_click_share_2nd': safe_get('product_click_share_2nd', 0.0, float),
                    'product_conversion_share_2nd': safe_get('product_conversion_share_2nd', 0.0, float),

                    # 第三名产品信息
                    'brand_3rd': safe_get('brand_3rd', ''),
                    'category_3rd': safe_get('category_3rd', ''),
                    'product_asin_3rd': safe_get('product_asin_3rd', ''),
                    'product_title_3rd': safe_get('product_title_3rd', ''),
                    'product_click_share_3rd': safe_get('product_click_share_3rd', 0.0, float),
                    'product_conversion_share_3rd': safe_get('product_conversion_share_3rd', 0.0, float),

                    # 状态标识
                    'is_new_day': data_type == 'daily',
                    'is_new_week': data_type == 'weekly',

                    # 时间戳
                    'created_at': current_time,
                    'updated_at': current_time
                }

                # 只添加有效记录（有关键词的）
                if record['keyword'].strip():
                    records.append(record)

            except Exception as e:
                logger.warning(f"转换记录失败，跳过该行: {e}")
                continue

        return records

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取CSV文件信息"""
        try:
            file_size = Path(file_path).stat().st_size

            # 估算行数（快速方法）
            with open(file_path, 'r', encoding='utf-8') as f:
                # 跳过前两行
                f.readline()
                f.readline()

                # 计算数据行数
                line_count = sum(1 for line in f if line.strip())

            return {
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'estimated_records': line_count,
                'estimated_chunks': (line_count // self.batch_size) + 1
            }

        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return {
                'file_size': 0,
                'file_size_mb': 0,
                'estimated_records': 0,
                'estimated_chunks': 0
            }


class FileValidator:
    """文件验证工具"""

    @staticmethod
    def validate_csv_structure(file_path: str) -> tuple[bool, str]:
        """验证CSV文件结构"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if len(lines) < 3:
                return False, "文件行数不足，至少需要3行（元数据、表头、数据）"

            # 检查第一行是否包含元数据
            first_line = lines[0].strip()
            if '报告范围' not in first_line:
                return False, "第一行应包含报告范围元数据"

            # 检查第二行是否是表头
            second_line = lines[1].strip()
            if '搜索频率排名' not in second_line or '搜索词' not in second_line:
                return False, "第二行应为表头，包含'搜索频率排名'和'搜索词'"

            # 检查第三行是否有数据
            if len(lines) > 2:
                third_line = lines[2].strip()
                if not third_line or len(third_line.split(',')) < 3:
                    return False, "第三行应包含实际数据"

            return True, "文件结构验证通过"

        except Exception as e:
            return False, f"文件验证失败: {str(e)}"

    @staticmethod
    def extract_file_metadata(file_path: str) -> Dict[str, Any]:
        """提取文件元数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()

            metadata = {}

            # 提取报告范围
            if '报告范围=' in first_line:
                range_match = first_line.split('报告范围=')[1].split(',')[0]
                metadata['report_range'] = range_match.strip('[]"')

            # 提取选择日期
            if '选择日期=' in first_line:
                date_match = first_line.split('选择日期=')[1].split(',')[0]
                metadata['selected_date'] = date_match.strip('[]"')

            return metadata

        except Exception as e:
            logger.error(f"提取文件元数据失败: {e}")
            return {}