
class TableComponent:
    """表格功能组件"""

    @staticmethod
    def build_data_table() -> dict:
        """构建数据表格 - 统一表头字体大小"""
        return {
            "type": "crud",
            "name": "data_table",
            "className": "analysis-table m-2",
            # API配置 - 支持所有查询参数
            "api": {
                "method": "get",
                "url": "/api/analysis/search",
                "data": {
                    # 分页参数
                    "page": "${page || 1}",
                    "perPage": "${perPage || 50}",

                    # 搜索条件参数
                    "keyword": "${keyword || ''}",
                    "brand": "${brand || ''}",
                    "category": "${category || ''}",
                    "asin": "${asin || ''}",
                    "product_title": "${product_title || ''}",
                    "daily_ranking_min": "${daily_ranking_min || ''}",
                    "daily_ranking_max": "${daily_ranking_max || ''}",
                    "daily_change_min": "${daily_change_min || ''}",
                    "daily_change_max": "${daily_change_max || ''}",
                    "weekly_ranking_min": "${weekly_ranking_min || ''}",
                    "weekly_ranking_max": "${weekly_ranking_max || ''}",
                    "weekly_change_min": "${weekly_change_min || ''}",
                    "weekly_change_max": "${weekly_change_max || ''}",
                    "click_share_min": "${click_share_min || ''}",
                    "click_share_max": "${click_share_max || ''}",
                    "conversion_share_min": "${conversion_share_min || ''}",
                    "conversion_share_max": "${conversion_share_max || ''}",
                    "conversion_rate_min": "${conversion_rate_min || ''}",
                    "conversion_rate_max": "${conversion_rate_max || ''}",
                    "is_new_day": "${is_new_day || ''}",
                    "is_new_week": "${is_new_week || ''}",
                    "report_date": "${report_date || ''}"
                }
            },

            # 默认参数
            "defaultParams": {
                "page": 1,
                "perPage": 50
            },

            # 表格列配置
            "columns": TableComponent._get_table_columns(),

            # 分页配置
            "perPage": 50,
            "perPageAvailable": [20, 50, 100, 200],
            "showPerPage": True,
            "showPageInput": True,

            # 表格工具栏配置
            "headerToolbar": [
                {
                    "type": "tpl",
                    "tpl": "共找到 ${count} 条记录",
                    "className": "analysis-toolbar"
                },
                "pagination"
            ],
            "footerToolbar": [
                "statistics",
                "pagination"
            ],

            # 表格其他配置
            "autoGenerateFilter": False,
            "syncLocation": False,
            "keepItemSelectionOnPageChange": True,
            "loadDataOnce": False,
            "loadDataOnceFetchOnFilter": True,

            # 表格样式
            "size": "sm",
            "bordered": True,
            "striped": True,
            "resizable": True,

            # 空数据提示
            "placeholder": "暂无数据，请尝试调整搜索条件"
        }

    @staticmethod
    def _get_table_columns() -> list:
        """获取表格列配置 - 统一表头字体，优化单元格显示"""
        return [
            # 序号列
            {
                "name": "id",
                "label": "序号",
                "width": 60,
                "type": "text",
                "sortable": False,
                "className": "text-center cell-narrow",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14"
            },

            # 关键词列 - 添加超链接和悬浮提示，不换行
            {
                "name": "keyword",
                "label": "关键词",
                "type": "tpl",
                "width": 140,
                "searchable": True,
                "className": "text-nowrap cell-wide",
                "style": {
                    "fontSize": "14px",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "textAlign": "left",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14",
                "tpl": "<a href='https://www.amazon.com/s?k=${keyword | url_encode}' target='_blank' class='keyword-link text-nowrap' title='${keyword}'>${keyword}</a>",
            },

            # 日排名
            {
                "name": "current_rangking_day",
                "label": "日排名",
                "type": "text",
                "width": 50,
                "sortable": True,
                "className": "text-center cell-narrow",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14"
            },

            # 日变化
            {
                "name": "ranking_change_day",
                "label": "日变化",
                "type": "tpl",
                "tpl": "<span class='${ranking_change_day > 0 ? \"change-positive\" : ranking_change_day < 0 ? \"change-negative\" : \"change-neutral\"}'>${ranking_change_day > 0 ? \"+\" + ranking_change_day : ranking_change_day}</span>",
                "width": 50,
                "sortable": True,
                "className": "text-center cell-narrow",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14"
            },

            # 周排名
            {
                "name": "current_rangking_week",
                "label": "周排名",
                "type": "text",
                "width": 50,
                "sortable": True,
                "className": "text-center cell-narrow",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14"
            },

            # 周变化
            {
                "name": "ranking_change_week",
                "label": "周变化",
                "type": "tpl",
                "tpl": "<span class='${ranking_change_week > 0 ? \"change-positive\" : ranking_change_week < 0 ? \"change-negative\" : \"change-neutral\"}'>${ranking_change_week > 0 ? \"+\" + ranking_change_week : ranking_change_week}</span>",
                "width": 50,
                "sortable": True,
                "className": "text-center cell-narrow",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14"
            },

            # 趋势图列
            {
                "name": "ranking_trend_day",
                "label": "排名趋势",
                "type": "tpl",
                "tpl": "<div class='trend-chart'>趋势图</div>",
                "width": 110,
                "sortable": False,
                "className": "text-center",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14"
            },

            # 品牌
            {
                "name": "top_brand",
                "label": "品牌",
                "type": "text",
                "width": 120,
                "searchable": True,
                "className": "text-nowrap cell-fixed-width",
                "style": {
                    "fontSize": "14px",
                    "whiteSpace": "nowrap",
                    "textAlign": "left",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14"
            },

            # 类目
            {
                "name": "top_category",
                "label": "类目",
                "type": "text",
                "width": 140,
                "searchable": True,
                "className": "text-nowrap cell-wide",
                "style": {
                    "fontSize": "14px",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "textAlign": "left",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14",
            },

            # ASIN - 显示编码，点击跳转，增加表头搜索
            {
                "name": "top_product_asin",
                "label": "ASIN",
                "type": "tpl",
                "width": 120,
                "searchable": True,
                "className": "cell-fixed-width",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14",
                "tpl": "<a href='https://www.amazon.com/dp/${top_product_asin}' target='_blank' class='asin-link' title='查看商品详情'>${top_product_asin}</a>"
            },

            # 商品标题 - 固定宽度，超出显示省略号，增加表头搜索
            {
                "name": "top_product_title",
                "label": "商品标题",
                "type": "text",
                "width": 200,
                "searchable": True,
                "className": "text-nowrap cell-wide",
                "style": {
                    "fontSize": "14px",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "textAlign": "left",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14",
            },

            # 点击份额
            {
                "name": "top_product_click_share",
                "label": "点击份额",
                "type": "tpl",
                "tpl": "<span>${top_product_click_share}%</span>",
                "width": 90,
                "sortable": True,
                "className": "text-center cell-narrow",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14"
            },

            # 转化份额
            {
                "name": "top_product_conversion_share",
                "label": "转化份额",
                "type": "tpl",
                "tpl": "<span>${top_product_conversion_share}%</span>",
                "width": 90,
                "sortable": True,
                "className": "text-center cell-narrow",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14"
            },

            # 转化率
            {
                "name": "conversion_rate",
                "label": "转化率",
                "type": "tpl",
                "tpl": "<span class='${conversion_rate >= 5 ? \"conversion-high\" : conversion_rate >= 2 ? \"conversion-medium\" : \"conversion-low\"}'>${conversion_rate}%</span>",
                "width": 80,
                "sortable": True,
                "className": "text-center cell-narrow",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14"
            },

            # 日新品
            {
                "name": "is_new_day",
                "label": "日新品",
                "type": "tpl",
                "width": 50,
                "className": "text-center cell-narrow",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14",
                "tpl": "<span class='${is_new_day ? \"status-new-day\" : \"status-normal\"}'>${is_new_day ? \"是\" : \"否\"}</span>"
            },

            # 周新品
            {
                "name": "is_new_week",
                "label": "周新品",
                "type": "tpl",
                "width": 50,
                "className": "text-center cell-narrow",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14",
                "tpl": "<span class='${is_new_week ? \"status-new-week\" : \"status-normal\"}'>${is_new_week ? \"是\" : \"否\"}</span>"
            },

            # 时间信息列
            {
                "name": "created_at",
                "label": "报告日期",
                "type": "datetime",
                "width": 140,
                "format": "YYYY-MM-DD HH:mm",
                "sortable": True,
                "className": "cell-fixed-width",
                "style": {
                    "fontSize": "14px",
                    "textAlign": "center",
                    "verticalAlign": "middle"
                },
                "labelClassName": "text-center vertical-middle font-size-14"
            }
        ]