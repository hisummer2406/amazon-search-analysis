# app/table/upload/csv_processor.py - 简化版：保留大文件处理核心功能
import logging
import pandas as pd
from typing import Iterator, Dict, Any, List
from pathlib import Path
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.table.analysis.analysis_model import AmazonOriginSearchData

logger = logging.getLogger(__name__)


class CSVProcessor:
    """CSV文件处理工具类 - 专为超大文件优化"""

    def __init__(self, batch_size: int = 5000):
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

    def process_chunk_with_upsert(
            self,
            df: pd.DataFrame,
            report_date: date,
            data_type: str,
            db_session: Session
    ) -> int:
        """处理数据块并执行去重更新逻辑"""
        processed_count = 0

        for _, row in df.iterrows():
            try:
                keyword = str(row.get('keyword', '')).strip()
                if not keyword:
                    continue

                # 查找现有记录
                existing_record = db_session.query(AmazonOriginSearchData).filter(
                    AmazonOriginSearchData.keyword == keyword
                ).first()

                current_ranking = int(float(row.get('current_rangking_day', 0))) if row.get(
                    'current_rangking_day') else 0

                if existing_record:
                    # 更新逻辑
                    if self._should_skip_update(existing_record, report_date, data_type):
                        continue
                    self._update_existing_record(existing_record, row, report_date, data_type, current_ranking)
                else:
                    # 插入新记录
                    new_record = self._create_new_record(row, report_date, data_type, current_ranking)
                    db_session.add(new_record)

                processed_count += 1

                # 批量提交
                if processed_count % 1000 == 0:
                    db_session.commit()

            except Exception as e:
                logger.warning(f"处理记录失败，跳过: {e}")
                continue

        db_session.commit()
        return processed_count

    def _should_skip_update(self, record: AmazonOriginSearchData, report_date: date, data_type: str) -> bool:
        """判断是否应跳过更新"""
        if data_type == 'daily':
            return record.report_date_day == report_date
        else:  # weekly
            return record.report_date_week == report_date

    def _update_existing_record(
            self,
            record: AmazonOriginSearchData,
            row: pd.Series,
            report_date: date,
            data_type: str,
            current_ranking: int
    ):
        """更新现有记录"""
        now = datetime.now()

        if data_type == 'daily':
            record.previous_rangking_day = record.current_rangking_day
            record.current_rangking_day = current_ranking
            record.ranking_change_day = current_ranking - record.previous_rangking_day
            record.report_date_day = report_date
            record.is_new_day = False
            self._update_trend_data(record, report_date, current_ranking)
        else:  # weekly
            record.previous_rangking_week = record.current_rangking_week
            record.current_rangking_week = current_ranking
            record.ranking_change_week = current_ranking - record.previous_rangking_week
            record.report_date_week = report_date
            record.is_new_week = False

        # 更新商品信息
        self._update_product_info(record, row)
        record.updated_at = now

    def _create_new_record(
            self,
            row: pd.Series,
            report_date: date,
            data_type: str,
            current_ranking: int
    ) -> AmazonOriginSearchData:
        """创建新记录"""
        now = datetime.now()

        record = AmazonOriginSearchData(
            keyword=str(row.get('keyword', '')).strip(),
            created_at=now,
            updated_at=now
        )

        if data_type == 'daily':
            record.current_rangking_day = current_ranking
            record.report_date_day = report_date
            record.previous_rangking_day = 0
            record.ranking_change_day = 0
            record.is_new_day = True
            record.ranking_trend_day = [{"date": report_date.isoformat(), "ranking": current_ranking}]
            # 周数据设置默认值
            record.current_rangking_week = 0
            record.report_date_week = report_date
            record.previous_rangking_week = 0
            record.ranking_change_week = 0
            record.is_new_week = False
        else:  # weekly
            record.current_rangking_week = current_ranking
            record.report_date_week = report_date
            record.previous_rangking_week = 0
            record.ranking_change_week = 0
            record.is_new_week = True
            # 日数据设置默认值
            record.current_rangking_day = 0
            record.report_date_day = report_date
            record.previous_rangking_day = 0
            record.ranking_change_day = 0
            record.is_new_day = False
            record.ranking_trend_day = []

        self._update_product_info(record, row)
        return record

    def _update_trend_data(self, record: AmazonOriginSearchData, report_date: date, ranking: int):
        """更新7天趋势数据"""
        trends = record.ranking_trend_day or []
        current_date_str = report_date.isoformat()

        # 使用字典去重，相同日期只保留最新数据
        trend_dict = {}
        for trend in trends:
            if isinstance(trend, dict) and "date" in trend and "ranking" in trend:
                trend_dict[trend["date"]] = int(trend["ranking"])

        # 更新或添加当前日期数据
        trend_dict[current_date_str] = ranking

        # 转换回列表，按日期排序，保留最近7天
        sorted_trends = sorted(trend_dict.items())[-7:]
        record.ranking_trend_day = [{"date": date_str, "ranking": rank} for date_str, rank in sorted_trends]

    def _update_product_info(self, record: AmazonOriginSearchData, row: pd.Series):
        """更新商品信息"""
        def safe_get(col, default='', dtype=str):
            val = row.get(col, default)
            if pd.isna(val) or val == '':
                return default if dtype == str else (0.0 if dtype == float else 0)
            try:
                return dtype(val) if dtype != str else str(val).strip()
            except:
                return default if dtype == str else (0.0 if dtype == float else 0)

        # Top产品信息
        record.top_brand = safe_get('top_brand')
        record.top_category = safe_get('top_category')
        record.top_product_asin = safe_get('top_product_asin')
        record.top_product_title = safe_get('top_product_title')
        record.top_product_click_share = safe_get('top_product_click_share', 0.0, float)
        record.top_product_conversion_share = safe_get('top_product_conversion_share', 0.0, float)

        # 第二名产品
        record.brand_2nd = safe_get('brand_2nd')
        record.category_2nd = safe_get('category_2nd')
        record.product_asin_2nd = safe_get('product_asin_2nd')
        record.product_title_2nd = safe_get('product_title_2nd')
        record.product_click_share_2nd = safe_get('product_click_share_2nd', 0.0, float)
        record.product_conversion_share_2nd = safe_get('product_conversion_share_2nd', 0.0, float)

        # 第三名产品
        record.brand_3rd = safe_get('brand_3rd')
        record.category_3rd = safe_get('category_3rd')
        record.product_asin_3rd = safe_get('product_asin_3rd')
        record.product_title_3rd = safe_get('product_title_3rd')
        record.product_click_share_3rd = safe_get('product_click_share_3rd', 0.0, float)
        record.product_conversion_share_3rd = safe_get('product_conversion_share_3rd', 0.0, float)

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