class TableComponent:
    """表格功能组件"""

    @staticmethod
    def build_data_table() -> dict:
        """构建数据表格 - 修复API参数传递"""
        return {
            "type": "crud",
            "name": "data_table",
            "className": "analysis-analysis m-2",
            # API配置 - 修复参数传递
            "api": {
                "method": "get",
                "url": "/api/analysis/search",
                "headers": {
                    "Authorization": "${ls:access_token ? 'Bearer ' + ls:access_token : ''}"
                },
                "data": {
                    # 分页参数
                    "page": "${page || 1}",
                    "perPage": "${perPage || 100}",

                    # 添加排序参数
                    "orderBy": "${orderBy}",
                    "orderDir": "${orderDir}",

                    # 基础搜索条件参数
                    "keyword": "${keyword}",
                    "brand": "${brand}",
                    "category": "${category}",
                    "asin": "${asin}",
                    "product_title": "${product_title}",
                    "report_date": "${report_date}",

                    # 高级搜索 - 排名范围参数
                    "daily_ranking_min": "${daily_ranking_min}",
                    "daily_ranking_max": "${daily_ranking_max}",
                    "weekly_ranking_min": "${weekly_ranking_min}",
                    "weekly_ranking_max": "${weekly_ranking_max}",

                    # 高级搜索 - 变化范围参数
                    "daily_change_min": "${daily_change_min}",
                    "daily_change_max": "${daily_change_max}",
                    "weekly_change_min": "${weekly_change_min}",
                    "weekly_change_max": "${weekly_change_max}",

                    # 高级搜索 - 份额和转化率范围参数
                    "click_share_min": "${click_share_min}",
                    "click_share_max": "${click_share_max}",
                    "conversion_share_min": "${conversion_share_min}",
                    "conversion_share_max": "${conversion_share_max}",
                    "conversion_rate_min": "${conversion_rate_min}",
                    "conversion_rate_max": "${conversion_rate_max}",

                    # 高级搜索 - 布尔值参数
                    "is_new_day": "${is_new_day}",
                    "is_new_week": "${is_new_week}"
                }
            },

            # 默认参数
            "defaultParams": {
                "page": 1,
                "perPage": 100
            },

            # 表格列配置
            "columns": TableComponent._get_table_columns(),

            # 分页配置
            "perPage": 100,
            "perPageAvailable": [100, 200, 500, 1000],
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
            # 关键词列 - 缩小宽度
            {
                "name": "keyword",
                "label": "关键词",
                "type": "tpl",
                "width": 80,
                "searchable": True,
                "className": "text-left cell-keyword",
                "labelClassName": "text-center vertical-middle font-size-14",
                "tpl": "<a href='https://www.amazon.com/s?k=${keyword | url_encode}' target='_blank' class='keyword-link' title='${keyword}'>${keyword}</a>",
            },

            # 排名列 - 保持紧凑
            {
                "name": "current_rangking_day",
                "label": "日排名",
                "type": "text",
                "width": 50,
                "sortable": True,
                "className": "text-center",
                "labelClassName": "text-center vertical-middle font-size-14"
            },
            {
                "name": "ranking_change_day",
                "label": "日变化",
                "type": "tpl",
                "tpl": "<span class='${ranking_change_day > 0 ? \"change-positive\" : ranking_change_day < 0 ? \"change-negative\" : \"change-neutral\"}'>${ranking_change_day > 0 ? \"+\" + ranking_change_day : ranking_change_day}</span>",
                "width": 50,
                "sortable": True,
                "className": "text-center",
                "labelClassName": "text-center vertical-middle font-size-14"
            },
            {
                "name": "current_rangking_week",
                "label": "周排名",
                "type": "text",
                "width": 50,
                "sortable": True,
                "className": "text-center",
                "labelClassName": "text-center vertical-middle font-size-14"
            },
            {
                "name": "ranking_change_week",
                "label": "周变化",
                "type": "tpl",
                "tpl": "<span class='${ranking_change_week > 0 ? \"change-positive\" : ranking_change_week < 0 ? \"change-negative\" : \"change-neutral\"}'>${ranking_change_week > 0 ? \"+\" + ranking_change_week : ranking_change_week}</span>",
                "width": 50,
                "sortable": True,
                "className": "text-center",
                "labelClassName": "text-center vertical-middle font-size-14"
            },

            # 趋势图列 - 修复版本
            {
                "name": "ranking_trend_day",
                "label": "排名趋势",
                "type": "chart",
                "width": 300,
                "sortable": False,
                "className": "text-center chart-cell",
                "labelClassName": "text-center vertical-middle font-size-14",
                "height": 200,
                "config": {
                    "dataset": {
                        "source": "${ranking_trend_day}"
                    },
                    "tooltip": {
                        "trigger": "axis",
                        "formatter": "function (params) { \
                        let item = params[0]; \
                        return '日期: ' + item.data.date + '<br/>排名: ' + item.data.ranking; \
                      }"
                    },

                    "xAxis": {
                        "type": "category"
                    },
                    "yAxis": {
                        "type": "value"
                    },
                    "series": [
                        {
                            "type": "line",
                            "smooth": True,
                            "encode": {
                                "x": "date",
                                "y": "ranking"
                            }
                        }
                    ]
                }
            },
            {
                "name": "top_category",
                "label": "类目",
                "type": "text",
                "width": 50,  # 从100减少到80
                "searchable": True,
                "className": "text-nowrap",
                "labelClassName": "text-center vertical-middle font-size-14",
            },

            # ASIN - 缩小宽度
            {
                "name": "top_product_asin",
                "label": "ASIN",
                "type": "tpl",
                "width": 50,  # 从100减少到80
                "searchable": True,
                "className": "text-center",
                "labelClassName": "text-center vertical-middle font-size-14",
                "tpl": "<a href='https://www.amazon.com/dp/${top_product_asin}' target='_blank' class='asin-link' title='查看商品详情'>${top_product_asin}</a>"
            },

            # 商品标题 - 大幅缩小，使用省略号
            {
                "name": "top_product_title",
                "label": "商品标题",
                "type": "text",
                "width": 100,
                "searchable": True,
                "className": "cell-title-ellipsis",
                "labelClassName": "text-center vertical-middle font-size-14",
            },

            # 数据指标列 - 缩小宽度
            {
                "name": "top_product_click_share",
                "label": "点击份额",
                "type": "tpl",
                "tpl": "<span>${top_product_click_share}%</span>",
                "width": 50,  # 从80减少到70
                "sortable": True,
                "className": "text-center",
                "labelClassName": "text-center vertical-middle font-size-14"
            },
            {
                "name": "top_product_conversion_share",
                "label": "转化份额",
                "type": "tpl",
                "tpl": "<span>${top_product_conversion_share}%</span>",
                "width": 50,
                "sortable": True,
                "className": "text-center",
                "labelClassName": "text-center vertical-middle font-size-14"
            },
            {
                "name": "conversion_rate",
                "label": "转化率",
                "type": "tpl",
                "tpl": "<span class='${conversion_rate >= 5 ? \"conversion-high\" : conversion_rate >= 2 ? \"conversion-medium\" : \"conversion-low\"}'>${conversion_rate}%</span>",
                "width": 50,
                "className": "text-center",
                "labelClassName": "text-center vertical-middle font-size-14"
            },

            # 状态列 - 缩小宽度
            {
                "name": "is_new_day",
                "label": "日新品",
                "type": "tpl",
                "width": 30,  # 从60减少到50
                "className": "text-center",
                "labelClassName": "text-center vertical-middle font-size-14",
                "tpl": "<span class='${is_new_day ? \"status-new-day\" : \"status-normal\"}'>${is_new_day ? \"是\" : \"否\"}</span>"
            },
            {
                "name": "is_new_week",
                "label": "周新品",
                "type": "tpl",
                "width": 30,
                "className": "text-center",
                "labelClassName": "text-center vertical-middle font-size-14",
                "tpl": "<span class='${is_new_week ? \"status-new-week\" : \"status-normal\"}'>${is_new_week ? \"是\" : \"否\"}</span>"
            },

            # 日期列 - 缩小宽度
            {
                "name": "report_date_day",
                "label": "报告日期",
                "type": "datetime",
                "width": 100,  # 从100减少到90
                "format": "YYYY-MM-DD",
                "sortable": True,
                "className": "text-center",
                "labelClassName": "text-center vertical-middle font-size-14"
            }
        ]
