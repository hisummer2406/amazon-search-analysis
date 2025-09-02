# app/table/upload/csv_processor.py - 优化版：使用 INSERT ... ON CONFLICT DO UPDATE
import logging
import pandas as pd
from typing import Iterator, Dict, Any, List
from pathlib import Path
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.table.analysis.analysis_model import AmazonOriginSearchData

logger = logging.getLogger(__name__)


class CSVProcessor:
    """CSV文件处理工具类 - 使用PostgreSQL UPSERT优化"""

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
        """使用PostgreSQL UPSERT批量处理数据块"""
        if len(df) == 0:
            return 0

        try:
            # 准备批量数据
            batch_data = []
            now = datetime.now()

            for _, row in df.iterrows():
                keyword = str(row.get('keyword', '')).strip()
                if not keyword:
                    continue

                current_ranking = int(float(row.get('current_rangking_day', 0))) if row.get(
                    'current_rangking_day') else 0
                record_data = self._prepare_record_data(row, report_date, data_type, current_ranking, now)
                batch_data.append(record_data)

            if not batch_data:
                return 0

            # 执行批量UPSERT - 逐条执行以避免批量绑定问题
            upsert_sql = self._build_upsert_sql(data_type)
            processed_count = 0

            for data in batch_data:
                try:
                    # 检查事务状态，如果中止则重新开始
                    if not db_session.is_active:
                        db_session.rollback()
                        db_session.begin()

                    db_session.execute(text(upsert_sql), data)
                    processed_count += 1
                except Exception as e:
                    logger.warning(f"单条记录UPSERT失败: {data.get('keyword', 'N/A')}, 错误: {e}")
                    # 发生错误时回滚当前事务
                    db_session.rollback()
                    db_session.begin()  # 开始新的事务
                    continue

            db_session.commit()
            return processed_count

        except Exception as e:
            db_session.rollback()
            logger.error(f"UPSERT处理失败: {e}")
            logger.error(f"错误详情: {str(e)}")
            raise

    def _build_upsert_sql(self, data_type: str) -> str:
        """构建UPSERT SQL语句 - 使用:param格式"""
        if data_type == 'daily':
            return """
                   INSERT INTO analysis.amazon_origin_search_data (keyword, created_at, updated_at, \
                                                                   current_rangking_day, report_date_day, \
                                                                   previous_rangking_day, \
                                                                   ranking_change_day, is_new_day, ranking_trend_day, \
                                                                   current_rangking_week, report_date_week, \
                                                                   previous_rangking_week, \
                                                                   ranking_change_week, is_new_week, \
                                                                   top_brand, top_category, top_product_asin, \
                                                                   top_product_title, \
                                                                   top_product_click_share, \
                                                                   top_product_conversion_share, \
                                                                   brand_2nd, category_2nd, product_asin_2nd, \
                                                                   product_title_2nd, \
                                                                   product_click_share_2nd, \
                                                                   product_conversion_share_2nd, \
                                                                   brand_3rd, category_3rd, product_asin_3rd, \
                                                                   product_title_3rd, \
                                                                   product_click_share_3rd, \
                                                                   product_conversion_share_3rd)
                   VALUES (:keyword, :created_at, :updated_at, \
                           :current_rangking_day, :report_date_day, :previous_rangking_day, \
                           :ranking_change_day, :is_new_day, CAST(:ranking_trend_day AS jsonb), \
                           :current_rangking_week, :report_date_week, :previous_rangking_week, \
                           :ranking_change_week, :is_new_week, \
                           :top_brand, :top_category, :top_product_asin, :top_product_title, \
                           :top_product_click_share, :top_product_conversion_share, \
                           :brand_2nd, :category_2nd, :product_asin_2nd, :product_title_2nd, \
                           :product_click_share_2nd, :product_conversion_share_2nd, \
                           :brand_3rd, :category_3rd, :product_asin_3rd, :product_title_3rd, \
                           :product_click_share_3rd, :product_conversion_share_3rd) ON CONFLICT (keyword) DO \
                   UPDATE SET
                       updated_at = EXCLUDED.updated_at, \
                       previous_rangking_day = CASE \
                       WHEN amazon_origin_search_data.report_date_day = EXCLUDED.report_date_day \
                       THEN amazon_origin_search_data.previous_rangking_day \
                       ELSE amazon_origin_search_data.current_rangking_day
                   END \
                   ,
                    current_rangking_day = EXCLUDED.current_rangking_day,
                    ranking_change_day = CASE 
                        WHEN amazon_origin_search_data.report_date_day = EXCLUDED.report_date_day 
                        THEN amazon_origin_search_data.ranking_change_day
                        ELSE EXCLUDED.current_rangking_day - amazon_origin_search_data.current_rangking_day
                   END \
                   ,
                    report_date_day = EXCLUDED.report_date_day,
                    is_new_day = CASE 
                        WHEN amazon_origin_search_data.report_date_day = EXCLUDED.report_date_day 
                        THEN amazon_origin_search_data.is_new_day
                        ELSE false
                   END \
                   ,
                    ranking_trend_day = CASE 
                        WHEN amazon_origin_search_data.report_date_day = EXCLUDED.report_date_day 
                        THEN (
                            -- 如果是同一天的数据，更新当天的排名
                            SELECT jsonb_agg(
                                CASE 
                                    WHEN item->>'date' = EXCLUDED.report_date_day::text 
                                    THEN jsonb_build_object('date', item->>'date', 'ranking', EXCLUDED.current_rangking_day)
                                    ELSE item
                                END
                            )
                            FROM jsonb_array_elements(amazon_origin_search_data.ranking_trend_day) AS item
                        )
                        ELSE (
                            -- 如果是新的一天，添加新数据并保留最近7天
                            WITH existing_items AS (
                                SELECT item
                                FROM jsonb_array_elements(amazon_origin_search_data.ranking_trend_day) AS item
                                WHERE (item->>'date')::date != EXCLUDED.report_date_day
                                ORDER BY (item->>'date')::date DESC
                                LIMIT 6
                            ),
                            new_item AS (
                                SELECT jsonb_build_object('date', EXCLUDED.report_date_day::text, 'ranking', EXCLUDED.current_rangking_day) AS item
                            ),
                            combined AS (
                                SELECT item FROM new_item
                                UNION ALL
                                SELECT item FROM existing_items
                            )
                            SELECT jsonb_agg(item ORDER BY (item->>'date')::date DESC)
                            FROM combined
                        )
                   END \
                   ,
                    top_brand = EXCLUDED.top_brand,
                    top_category = EXCLUDED.top_category,
                    top_product_asin = EXCLUDED.top_product_asin,
                    top_product_title = EXCLUDED.top_product_title,
                    top_product_click_share = EXCLUDED.top_product_click_share,
                    top_product_conversion_share = EXCLUDED.top_product_conversion_share,
                    brand_2nd = EXCLUDED.brand_2nd,
                    category_2nd = EXCLUDED.category_2nd,
                    product_asin_2nd = EXCLUDED.product_asin_2nd,
                    product_title_2nd = EXCLUDED.product_title_2nd,
                    product_click_share_2nd = EXCLUDED.product_click_share_2nd,
                    product_conversion_share_2nd = EXCLUDED.product_conversion_share_2nd,
                    brand_3rd = EXCLUDED.brand_3rd,
                    category_3rd = EXCLUDED.category_3rd,
                    product_asin_3rd = EXCLUDED.product_asin_3rd,
                    product_title_3rd = EXCLUDED.product_title_3rd,
                    product_click_share_3rd = EXCLUDED.product_click_share_3rd,
                    product_conversion_share_3rd = EXCLUDED.product_conversion_share_3rd \
                   """
        else:  # weekly
            # 周数据的SQL保持不变
            return """
                   INSERT INTO analysis.amazon_origin_search_data (keyword, created_at, updated_at, \
                                                                   current_rangking_week, report_date_week, \
                                                                   previous_rangking_week, \
                                                                   ranking_change_week, is_new_week, \
                                                                   current_rangking_day, report_date_day, \
                                                                   previous_rangking_day, \
                                                                   ranking_change_day, is_new_day, ranking_trend_day, \
                                                                   top_brand, top_category, top_product_asin, \
                                                                   top_product_title, \
                                                                   top_product_click_share, \
                                                                   top_product_conversion_share, \
                                                                   brand_2nd, category_2nd, product_asin_2nd, \
                                                                   product_title_2nd, \
                                                                   product_click_share_2nd, \
                                                                   product_conversion_share_2nd, \
                                                                   brand_3rd, category_3rd, product_asin_3rd, \
                                                                   product_title_3rd, \
                                                                   product_click_share_3rd, \
                                                                   product_conversion_share_3rd)
                   VALUES (:keyword, :created_at, :updated_at, \
                           :current_rangking_week, :report_date_week, :previous_rangking_week, \
                           :ranking_change_week, :is_new_week, \
                           :current_rangking_day, :report_date_day, :previous_rangking_day, \
                           :ranking_change_day, :is_new_day, CAST(:ranking_trend_day AS jsonb), \
                           :top_brand, :top_category, :top_product_asin, :top_product_title, \
                           :top_product_click_share, :top_product_conversion_share, \
                           :brand_2nd, :category_2nd, :product_asin_2nd, :product_title_2nd, \
                           :product_click_share_2nd, :product_conversion_share_2nd, \
                           :brand_3rd, :category_3rd, :product_asin_3rd, :product_title_3rd, \
                           :product_click_share_3rd, :product_conversion_share_3rd) ON CONFLICT (keyword) DO \
                   UPDATE SET
                       updated_at = EXCLUDED.updated_at, \
                       previous_rangking_week = CASE \
                       WHEN amazon_origin_search_data.report_date_week = EXCLUDED.report_date_week \
                       THEN amazon_origin_search_data.previous_rangking_week \
                       ELSE amazon_origin_search_data.current_rangking_week
                   END \
                   ,
                    current_rangking_week = EXCLUDED.current_rangking_week,
                    ranking_change_week = CASE 
                        WHEN amazon_origin_search_data.report_date_week = EXCLUDED.report_date_week 
                        THEN amazon_origin_search_data.ranking_change_week
                        ELSE EXCLUDED.current_rangking_week - amazon_origin_search_data.current_rangking_week
                   END \
                   ,
                    report_date_week = EXCLUDED.report_date_week,
                    is_new_week = CASE 
                        WHEN amazon_origin_search_data.report_date_week = EXCLUDED.report_date_week 
                        THEN amazon_origin_search_data.is_new_week
                        ELSE false
                   END \
                   ,
                    top_brand = EXCLUDED.top_brand,
                    top_category = EXCLUDED.top_category,
                    top_product_asin = EXCLUDED.top_product_asin,
                    top_product_title = EXCLUDED.top_product_title,
                    top_product_click_share = EXCLUDED.top_product_click_share,
                    top_product_conversion_share = EXCLUDED.top_product_conversion_share,
                    brand_2nd = EXCLUDED.brand_2nd,
                    category_2nd = EXCLUDED.category_2nd,
                    product_asin_2nd = EXCLUDED.product_asin_2nd,
                    product_title_2nd = EXCLUDED.product_title_2nd,
                    product_click_share_2nd = EXCLUDED.product_click_share_2nd,
                    product_conversion_share_2nd = EXCLUDED.product_conversion_share_2nd,
                    brand_3rd = EXCLUDED.brand_3rd,
                    category_3rd = EXCLUDED.category_3rd,
                    product_asin_3rd = EXCLUDED.product_asin_3rd,
                    product_title_3rd = EXCLUDED.product_title_3rd,
                    product_click_share_3rd = EXCLUDED.product_click_share_3rd,
                    product_conversion_share_3rd = EXCLUDED.product_conversion_share_3rd \
                   """

    def _prepare_record_data(self, row: pd.Series, report_date: date, data_type: str, current_ranking: int,
                             now: datetime) -> Dict[str, Any]:
        """准备记录数据"""

        def safe_get(col, default='', dtype=str):
            val = row.get(col, default)
            if pd.isna(val) or val == '':
                return default if dtype == str else (0.0 if dtype == float else 0)
            try:
                return dtype(val) if dtype != str else str(val).strip()
            except:
                return default if dtype == str else (0.0 if dtype == float else 0)

        # 基础数据
        data = {
            'keyword': str(row.get('keyword', '')).strip(),
            'created_at': now,
            'updated_at': now,
            'report_date': report_date,
            'current_ranking': current_ranking,

            # 商品信息
            'top_brand': safe_get('top_brand'),
            'top_category': safe_get('top_category'),
            'top_product_asin': safe_get('top_product_asin'),
            'top_product_title': safe_get('top_product_title'),
            'top_product_click_share': safe_get('top_product_click_share', 0.0, float),
            'top_product_conversion_share': safe_get('top_product_conversion_share', 0.0, float),

            'brand_2nd': safe_get('brand_2nd'),
            'category_2nd': safe_get('category_2nd'),
            'product_asin_2nd': safe_get('product_asin_2nd'),
            'product_title_2nd': safe_get('product_title_2nd'),
            'product_click_share_2nd': safe_get('product_click_share_2nd', 0.0, float),
            'product_conversion_share_2nd': safe_get('product_conversion_share_2nd', 0.0, float),

            'brand_3rd': safe_get('brand_3rd'),
            'category_3rd': safe_get('category_3rd'),
            'product_asin_3rd': safe_get('product_asin_3rd'),
            'product_title_3rd': safe_get('product_title_3rd'),
            'product_click_share_3rd': safe_get('product_click_share_3rd', 0.0, float),
            'product_conversion_share_3rd': safe_get('product_conversion_share_3rd', 0.0, float),
        }

        import json

        # 根据数据类型设置特定字段
        if data_type == 'daily':
            ranking_trend_data = [{"date": report_date.isoformat(), "ranking": current_ranking}]

            data.update({
                'current_rangking_day': current_ranking,
                'report_date_day': report_date,
                'previous_rangking_day': 0,  # 由数据库处理
                'ranking_change_day': 0,  # 由数据库计算
                'is_new_day': True,  # 由数据库处理
                'ranking_trend_day': json.dumps(ranking_trend_data),

                # 周数据默认值
                'current_rangking_week': 0,
                'report_date_week': report_date,
                'previous_rangking_week': 0,
                'ranking_change_week': 0,
                'is_new_week': False
            })
        else:  # weekly
            data.update({
                'current_rangking_week': current_ranking,
                'report_date_week': report_date,
                'previous_rangking_week': 0,  # 由数据库处理
                'ranking_change_week': 0,  # 由数据库计算
                'is_new_week': True,  # 由数据库处理

                # 日数据默认值
                'current_rangking_day': 0,
                'report_date_day': report_date,
                'previous_rangking_day': 0,
                'ranking_change_day': 0,
                'is_new_day': False,
                'ranking_trend_day': '[]'
            })

        return data


    # 保持原有的辅助方法不变
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
