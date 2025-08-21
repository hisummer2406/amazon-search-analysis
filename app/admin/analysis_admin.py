from fastapi_amis_admin.admin import admin
from fastapi_amis_admin.amis import PageSchema, Page
from app.admin.admin_site import site


# 主要数据查询页面
@site.register_admin
class AmazonDataQueryAdmin(admin.PageAdmin):
    """主要数据查询页面"""
    page_schema = PageSchema(
        label="数据查询",
        icon="fa fa-search",
        isDefaultPage=True,
        sort=1
    )

    async def get_page(self, request) -> Page:
        # 顶部搜索条件区域
        search_conditions = {
            "type": "form",
            "mode": "horizontal",
            "target": "search_results",
            "className": "m-2",
            "body": [
                # 第一行搜索条件
                {
                    "type": "group",
                    "body": [
                        {
                            "type": "input-text",
                            "name": "关键词",
                            "label": "关键词:",
                            "placeholder": "请输入配",
                            "size": "sm",
                            "className": "w-40"
                        },
                        {
                            "type": "select",
                            "name": "日排名",
                            "label": "日排名:",
                            "placeholder": "-",
                            "size": "sm",
                            "className": "w-32",
                            "options": []
                        },
                        {
                            "type": "select",
                            "name": "日变化",
                            "label": "日变化:",
                            "placeholder": "-",
                            "size": "sm",
                            "className": "w-32",
                            "options": []
                        },
                        {
                            "type": "select",
                            "name": "周排名",
                            "label": "周排名:",
                            "placeholder": "-",
                            "size": "sm",
                            "className": "w-32",
                            "options": []
                        },
                        {
                            "type": "select",
                            "name": "周变化",
                            "label": "周变化:",
                            "placeholder": "-",
                            "size": "sm",
                            "className": "w-32",
                            "options": []
                        },
                        {
                            "type": "select",
                            "name": "类目",
                            "label": "类目:",
                            "placeholder": "全部",
                            "size": "sm",
                            "className": "w-40",
                            "options": []
                        }
                    ]
                },
                # 第二行搜索条件
                {
                    "type": "group",
                    "body": [
                        {
                            "type": "select",
                            "name": "周周变化",
                            "label": "周周变化:",
                            "value": "ALL",
                            "size": "sm",
                            "className": "w-32",
                            "options": [
                                {"label": "ALL", "value": "ALL"}
                            ]
                        },
                        {
                            "type": "select",
                            "name": "总变化",
                            "label": "总变化:",
                            "placeholder": "-",
                            "size": "sm",
                            "className": "w-32",
                            "options": []
                        },
                        {
                            "type": "input-text",
                            "name": "点击份额",
                            "label": "点击份额:",
                            "placeholder": "-",
                            "size": "sm",
                            "className": "w-32"
                        },
                        {
                            "type": "input-text",
                            "name": "转化份额",
                            "label": "转化份额:",
                            "placeholder": "-",
                            "size": "sm",
                            "className": "w-32"
                        },
                        {
                            "type": "input-text",
                            "name": "转化率",
                            "label": "转化率:",
                            "placeholder": "-",
                            "size": "sm",
                            "className": "w-32"
                        },
                        {
                            "type": "select",
                            "name": "是否日期新",
                            "label": "是否日期新:",
                            "placeholder": "-",
                            "size": "sm",
                            "className": "w-40",
                            "options": []
                        },
                        {
                            "type": "select",
                            "name": "是否周新数",
                            "label": "是否周新数:",
                            "placeholder": "-",
                            "size": "sm",
                            "className": "w-40",
                            "options": []
                        },
                        {
                            "type": "select",
                            "name": "是否周有日一",
                            "label": "是否周有日一:",
                            "placeholder": "-",
                            "size": "sm",
                            "className": "w-40",
                            "options": []
                        },
                        {
                            "type": "input-date",
                            "name": "日期日期",
                            "label": "日期日期:",
                            "size": "sm",
                            "className": "w-40"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "submit",
                    "label": "查询",
                    "level": "primary",
                    "size": "sm"
                },
                {
                    "type": "button",
                    "label": "上传日数据",
                    "level": "success",
                    "size": "sm",
                    "actionType": "dialog",
                    "dialog": {
                        "title": "上传日数据",
                        "body": {
                            "type": "form",
                            "api": "post:/api/upload/upload-csv",
                            "body": [
                                {
                                    "type": "input-file",
                                    "name": "file",
                                    "label": "选择CSV文件",
                                    "accept": ".csv",
                                    "required": True
                                },
                                {
                                    "type": "hidden",
                                    "name": "data_type",
                                    "value": "daily"
                                },
                                {
                                    "type": "input-date",
                                    "name": "report_date",
                                    "label": "报告日期",
                                    "required": True,
                                    "format": "YYYY-MM-DD"
                                }
                            ]
                        }
                    }
                },
                {
                    "type": "button",
                    "label": "上传周数据",
                    "level": "info",
                    "size": "sm",
                    "actionType": "dialog",
                    "dialog": {
                        "title": "上传周数据",
                        "body": {
                            "type": "form",
                            "api": "post:/api/upload/upload-csv",
                            "body": [
                                {
                                    "type": "input-file",
                                    "name": "file",
                                    "label": "选择CSV文件",
                                    "accept": ".csv",
                                    "required": True
                                },
                                {
                                    "type": "hidden",
                                    "name": "data_type",
                                    "value": "weekly"
                                },
                                {
                                    "type": "input-date",
                                    "name": "report_date",
                                    "label": "报告日期",
                                    "required": True,
                                    "format": "YYYY-MM-DD"
                                }
                            ]
                        }
                    }
                }
            ]
        }

        # 表格数据区域 - 按照图片中的表格结构
        data_table = {
            "type": "service",
            "name": "search_results",
            "api": "/api/analytics/search",
            "body": {
                "type": "table",
                "source": "${data}",
                "columns": [
                    # 序号列
                    {
                        "name": "id",
                        "label": "",
                        "width": 50,
                        "type": "text"
                    },
                    # 关键词列（带链接）
                    {
                        "name": "keyword",
                        "label": "关键词",
                        "type": "link",
                        "width": 120
                    },
                    # 数值列组
                    {
                        "name": "current_rangking_day",
                        "label": "当前日",
                        "type": "number",
                        "width": 80
                    },
                    {
                        "name": "previous_rangking_day",
                        "label": "上期日",
                        "type": "number",
                        "width": 80
                    },
                    {
                        "name": "ranking_change_day",
                        "label": "日变化",
                        "type": "number",
                        "width": 80
                    },
                    {
                        "name": "current_rangking_week",
                        "label": "当前周",
                        "type": "number",
                        "width": 80
                    },
                    {
                        "name": "previous_rangking_week",
                        "label": "上期周",
                        "type": "number",
                        "width": 80
                    },
                    {
                        "name": "ranking_change_week",
                        "label": "周变化",
                        "type": "number",
                        "width": 80
                    },
                    # 趋势图列
                    {
                        "name": "ranking_trend_day",
                        "label": "趋势图",
                        "type": "tpl",
                        "tpl": "<div style='width:120px;height:60px;background:#f5f5f5;'></div>",
                        "width": 150
                    },
                    # 商品信息列
                    {
                        "name": "top_brand",
                        "label": "品牌",
                        "type": "text",
                        "width": 100
                    },
                    {
                        "name": "top_category",
                        "label": "类目",
                        "type": "text",
                        "width": 80
                    },
                    {
                        "name": "top_product_asin",
                        "label": "ASIN",
                        "type": "link",
                        "width": 100
                    },
                    {
                        "name": "top_product_title",
                        "label": "标题",
                        "type": "text",
                        "width": 200
                    },
                    # 数据指标列
                    {
                        "name": "top_product_click_share",
                        "label": "点击份额",
                        "type": "number",
                        "width": 80
                    },
                    {
                        "name": "top_product_conversion_share",
                        "label": "转化份额",
                        "type": "number",
                        "width": 80
                    },
                    {
                        "name": "conversion_rate",
                        "label": "转化率",
                        "type": "number",
                        "width": 80
                    },
                    {
                        "name": "is_new_day",
                        "label": "日新品",
                        "type": "switch",
                        "width": 80
                    },
                    {
                        "name": "is_new_week",
                        "label": "周新品",
                        "type": "switch",
                        "width": 80
                    },
                    # 日期列
                    {
                        "name": "report_date_day",
                        "label": "周商品一",
                        "type": "date",
                        "width": 100
                    },
                    {
                        "name": "report_date_week",
                        "label": "日期日期",
                        "type": "date",
                        "width": 100
                    },
                    {
                        "name": "created_at",
                        "label": "报告日期",
                        "type": "datetime",
                        "width": 120
                    }
                ],
                # 分页配置
                "pagination": {
                    "perPage": 50,
                    "perPageAvailable": [50, 100, 200],
                    "showPerPage": True,
                    "showPageInput": True
                },
                # 表格配置
                "headerToolbar": [
                    "pagination",
                    {
                        "type": "tpl",
                        "tpl": "显示第1到50，共25343条",
                        "className": "text-muted"
                    }
                ],
                "footerToolbar": ["pagination"]
            }
        }

        return Page(
            title="数据查询",
            body=[
                search_conditions,
                {"type": "divider"},
                data_table
            ]
        )
