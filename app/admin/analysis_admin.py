from fastapi_amis_admin.admin import admin
from fastapi_amis_admin.amis import PageSchema, Page
from app.admin.admin_site import site
from fastapi import Request


@site.register_admin
class AmazonDataQueryAdmin(admin.PageAdmin):
    """主要数据查询页面"""
    page_schema = PageSchema(
        label="数据查询",
        icon="fa fa-search",
        isDefaultPage=True,
        sort=1
    )

    async def get_page(self, request: Request) -> Page:
        # 顶部搜索条件区域
        search_conditions = self._build_search_form()

        # 表格数据区域 - 使用CRUD组件支持完整分页功能
        data_table = self._build_data_table()

        # 自定义CSS样式
        custom_css = {
            "type": "html",
            "html": """
            <style>
                .font-size-14 { font-size: 14px !important; }
                .font-size-16 { font-size: 16px !important; }
                .text-nowrap { white-space: nowrap !important; overflow: hidden; text-overflow: ellipsis; }
                .table-responsive .table td { vertical-align: middle; }
                .form-control { font-size: 14px; }
                .btn { font-size: 14px; }
            </style>
            """
        }

        return Page(
            title="数据查询",
            body=[
                custom_css,
                search_conditions,
                {"type": "divider"},
                data_table
            ]
        )

    def _build_search_form(self) -> dict:
        """构建搜索表单"""
        return {
            "type": "form",
            "target": "data_table",
            "className": "bg-white p-3 mb-3 border rounded",
            "wrapWithPanel": False,
            "body": [
                # 第一行
                {
                    "type": "flex",
                    "className": "mb-3",
                    "items": [
                        {
                            "type": "input-text",
                            "name": "keyword",
                            "label": "关键词",
                            "placeholder": "请输入关键词",
                            "labelWidth": 80,
                            "className": "flex-1 mr-3"
                        },
                        {
                            "type": "select",
                            "name": "daily_ranking",
                            "label": "日排名",
                            "placeholder": "全部",
                            "labelWidth": 80,
                            "className": "flex-1 mr-3",
                            "clearable": True,
                            "options": [
                                {"label": "1-10", "value": "1-10"},
                                {"label": "11-20", "value": "11-20"},
                                {"label": "21-50", "value": "21-50"},
                                {"label": ">50", "value": ">50"},
                                {"label": ">100", "value": ">100"}
                            ]
                        },
                        {
                            "type": "select",
                            "name": "daily_change",
                            "label": "日变化",
                            "placeholder": "全部",
                            "labelWidth": 80,
                            "className": "flex-1 mr-3",
                            "clearable": True,
                            "options": [
                                {"label": "上升>10", "value": ">10"},
                                {"label": "上升1-10", "value": "1-10"},
                                {"label": "不变", "value": "=0"},
                                {"label": "下降1-10", "value": "-10-0"},
                                {"label": "下降>10", "value": "<-10"}
                            ]
                        },
                        {
                            "type": "select",
                            "name": "category",
                            "label": "类目",
                            "placeholder": "全部",
                            "labelWidth": 80,
                            "className": "flex-1",
                            "clearable": True,
                            "searchable": True,
                            "options": []
                        }
                    ]
                },
                # 第二行
                {
                    "type": "flex",
                    "className": "mb-3",
                    "items": [
                        {
                            "type": "select",
                            "name": "weekly_ranking",
                            "label": "周排名",
                            "placeholder": "全部",
                            "labelWidth": 80,
                            "className": "flex-1 mr-3",
                            "clearable": True,
                            "options": [
                                {"label": "1-10", "value": "1-10"},
                                {"label": "11-20", "value": "11-20"},
                                {"label": "21-50", "value": "21-50"},
                                {"label": ">50", "value": ">50"},
                                {"label": ">100", "value": ">100"}
                            ]
                        },
                        {
                            "type": "select",
                            "name": "weekly_change",
                            "label": "周变化",
                            "placeholder": "全部",
                            "labelWidth": 80,
                            "className": "flex-1 mr-3",
                            "clearable": True,
                            "options": [
                                {"label": "上升>10", "value": ">10"},
                                {"label": "上升1-10", "value": "1-10"},
                                {"label": "不变", "value": "=0"},
                                {"label": "下降1-10", "value": "-10-0"},
                                {"label": "下降>10", "value": "<-10"}
                            ]
                        },
                        {
                            "type": "select",
                            "name": "is_new_day",
                            "label": "日新品",
                            "placeholder": "全部",
                            "labelWidth": 80,
                            "className": "flex-1 mr-3",
                            "clearable": True,
                            "options": [
                                {"label": "是", "value": True},
                                {"label": "否", "value": False}
                            ]
                        },
                        {
                            "type": "input-date",
                            "name": "report_date",
                            "label": "报告日期",
                            "labelWidth": 80,
                            "className": "flex-1",
                            "format": "YYYY-MM-DD",
                            "clearable": True
                        }
                    ]
                },
                # 操作按钮行
                {
                    "type": "flex",
                    "justify": "space-between",
                    "items": [
                        {
                            "type": "flex",
                            "items": [
                                {
                                    "type": "submit",
                                    "label": "查询",
                                    "level": "primary",
                                    "className": "mr-2"
                                },
                                {
                                    "type": "reset",
                                    "label": "重置",
                                    "className": "mr-2"
                                }
                            ]
                        },
                        {
                            "type": "flex",
                            "items": [
                                {
                                    "type": "button",
                                    "label": "上传日数据",
                                    "level": "success",
                                    "className": "mr-2",
                                    "actionType": "dialog",
                                    "dialog": self._get_upload_dialog("daily", "上传日数据")
                                },
                                {
                                    "type": "button",
                                    "label": "上传周数据",
                                    "level": "info",
                                    "actionType": "dialog",
                                    "dialog": self._get_upload_dialog("weekly", "上传周数据")
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    def _build_data_table(self) -> dict:
        """构建数据表格 - 使用CRUD组件支持完整分页"""
        return {
            "type": "crud",
            "name": "data_table",
            "className": "m-2",
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
                    "daily_ranking": "${daily_ranking || ''}",
                    "daily_change": "${daily_change || ''}",
                    "weekly_ranking": "${weekly_ranking || ''}",
                    "weekly_change": "${weekly_change || ''}",
                    "category": "${category || ''}",
                    "click_share_min": "${click_share_min || ''}",
                    "click_share_max": "${click_share_max || ''}",
                    "conversion_share_min": "${conversion_share_min || ''}",
                    "conversion_share_max": "${conversion_share_max || ''}",
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
            "columns": self._get_table_columns(),

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
                    "className": "text-muted"
                },
                "pagination"
            ],
            "footerToolbar": [
                "statistics",
                "pagination"
            ],

            # 表格其他配置
            "autoGenerateFilter": False,  # 关闭自动生成过滤器
            "syncLocation": False,  # 不同步URL参数
            "keepItemSelectionOnPageChange": True,  # 翻页保持选择
            "loadDataOnce": False,  # 每次都重新加载数据
            "loadDataOnceFetchOnFilter": True,  # 过滤时重新加载

            # 表格样式
            "size": "md",  # 改为中等大小字体
            "bordered": True,
            "striped": True,
            "resizable": True,
            "className": "table-responsive",

            # 表格内容样式
            "rowClassName": "font-size-14",  # 行字体大小

            # 空数据提示
            "placeholder": "暂无数据，请尝试调整搜索条件"
        }

    def _get_table_columns(self) -> list:
        """获取表格列配置 - 移除列分组避免兼容性问题"""
        return [
            # 序号列
            {
                "name": "id",
                "label": "序号",
                "width": 80,
                "type": "text",
                "sortable": False,
                "className": "text-center font-size-16"
            },

            # 关键词列 - 不换行
            {
                "name": "keyword",
                "label": "关键词",
                "type": "text",
                "width": 150,
                "searchable": True,
                "sortable": True,
                "className": "font-weight-bold text-nowrap font-size-16"
            },

            # 日排名 - 直接显示数据库字段
            {
                "name": "current_rangking_day",
                "label": "日排名",
                "type": "text",
                "width": 100,
                "sortable": True,
                "className": "text-center font-size-16"
            },

            # 日变化 - 上周期减去本周期
            {
                "name": "ranking_change_day",
                "label": "日变化",
                "type": "tpl",
                "tpl": "<span class='${ranking_change_day > 0 ? \"text-success\" : ranking_change_day < 0 ? \"text-danger\" : \"text-muted\"} font-size-16'>${ranking_change_day > 0 ? \"+\" + ranking_change_day : ranking_change_day}</span>",
                "width": 100,
                "sortable": True,
                "className": "text-center"
            },

            # 周排名 - 直接显示数据库字段
            {
                "name": "current_rangking_week",
                "label": "周排名",
                "type": "text",
                "width": 100,
                "sortable": True,
                "className": "text-center font-size-16"
            },

            # 周变化 - 上周期减去本周期
            {
                "name": "ranking_change_week",
                "label": "周变化",
                "type": "tpl",
                "tpl": "<span class='${ranking_change_week > 0 ? \"text-success\" : ranking_change_week < 0 ? \"text-danger\" : \"text-muted\"} font-size-16'>${ranking_change_week > 0 ? \"+\" + ranking_change_week : ranking_change_week}</span>",
                "width": 100,
                "sortable": True,
                "className": "text-center"
            },

            # 趋势图列
            {
                "name": "ranking_trend_day",
                "label": "排名趋势",
                "type": "tpl",
                "tpl": "<div class='trend-chart' style='width:120px;height:40px;background:linear-gradient(90deg, #e3f2fd 0%, #bbdefb 50%, #90caf9 100%);border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:14px;color:#1976d2;'>趋势图</div>",
                "width": 140,
                "sortable": False
            },

            # 品牌
            {
                "name": "top_brand",
                "label": "品牌",
                "type": "text",
                "width": 120,
                "searchable": True,
                "className": "text-nowrap font-size-16"
            },

            # 类目
            {
                "name": "top_category",
                "label": "类目",
                "type": "text",
                "width": 120,
                "searchable": True,
                "className": "text-nowrap font-size-16"
            },

            # ASIN - 显示编码，点击跳转
            {
                "name": "top_product_asin",
                "label": "ASIN",
                "type": "link",
                "href": "https://www.amazon.com/dp/${top_product_asin}",
                "target": "_blank",
                "width": 120,
                "className": "text-primary font-size-16"
            },

            # 商品标题 - 不换行显示
            {
                "name": "top_product_title",
                "label": "商品标题",
                "type": "text",
                "width": 250,
                "className": "text-nowrap font-size-16",
                "popOver": {
                    "body": "${top_product_title}",
                    "trigger": "hover"
                }
            },

            # 点击份额
            {
                "name": "top_product_click_share",
                "label": "点击份额",
                "type": "tpl",
                "tpl": "<span class='font-size-16'>${top_product_click_share}%</span>",
                "width": 100,
                "sortable": True,
                "className": "text-center"
            },

            # 转化份额
            {
                "name": "top_product_conversion_share",
                "label": "转化份额",
                "type": "tpl",
                "tpl": "<span class='font-size-16'>${top_product_conversion_share}%</span>",
                "width": 100,
                "sortable": True,
                "className": "text-center"
            },

            # 转化率
            {
                "name": "conversion_rate",
                "label": "转化率",
                "type": "tpl",
                "tpl": "<span class='${conversion_rate >= 5 ? \"text-success\" : conversion_rate >= 2 ? \"text-warning\" : \"text-danger\"} font-size-16'>${conversion_rate}%</span>",
                "width": 100,
                "sortable": True,
                "className": "text-center"
            },

            # 日新品
            {
                "name": "is_new_day",
                "label": "日新品",
                "type": "status",
                "width": 100,
                "className": "font-size-16",
                "map": {
                    "true": {
                        "value": 1,
                        "label": "是",
                        "color": "success"
                    },
                    "false": {
                        "value": 0,
                        "label": "否",
                        "color": "default"
                    }
                }
            },

            # 周新品
            {
                "name": "is_new_week",
                "label": "周新品",
                "type": "status",
                "width": 100,
                "className": "font-size-16",
                "map": {
                    "true": {
                        "value": 1,
                        "label": "是",
                        "color": "info"
                    },
                    "false": {
                        "value": 0,
                        "label": "否",
                        "color": "default"
                    }
                }
            },

            # 时间信息列
            {
                "name": "created_at",
                "label": "报告日期",
                "type": "datetime",
                "width": 160,
                "format": "YYYY-MM-DD HH:mm",
                "sortable": True,
                "className": "font-size-16"
            }
        ]

    def _get_upload_dialog(self, data_type: str, title: str) -> dict:
        """获取上传对话框配置"""
        return {
            "title": title,
            "size": "md",
            "body": {
                "type": "form",
                "api": {
                    "method": "post",
                    "url": "/api/upload/upload-csv"
                },
                "body": [
                    {
                        "type": "input-file",
                        "name": "file",
                        "label": "选择CSV文件",
                        "accept": ".csv",
                        "required": True,
                        "drag": True,
                        "description": f"请选择{title}的CSV文件，文件大小限制3GB"
                    },
                    {
                        "type": "hidden",
                        "name": "data_type",
                        "value": data_type
                    },
                    {
                        "type": "input-date",
                        "name": "report_date",
                        "label": "报告日期",
                        "required": True,
                        "format": "YYYY-MM-DD",
                        "description": "请选择数据对应的报告日期"
                    }
                ]
            },
            "actions": [
                {
                    "type": "button",
                    "label": "取消",
                    "actionType": "cancel"
                },
                {
                    "type": "submit",
                    "label": "开始上传",
                    "level": "primary"
                }
            ]
        }
