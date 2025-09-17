"""
搜索组件 - 修复高级搜索打不开的问题，优化参数传递
"""


class SearchComponent:
    """搜索功能组件"""

    @staticmethod
    def build_search_form() -> dict:
        """构建搜索表单 - 修复高级搜索显示问题，优化参数传递"""
        return {
            "type": "form",
            "target": "data_table",
            "className": "search-form",
            "wrapWithPanel": False,
            "body": [
                # 第一行：基础搜索条件
                {
                    "type": "flex",
                    "className": "mb-2",
                    "items": [
                        {
                            "type": "flex",
                            "className": "flex-1 mr-3",
                            "items": [
                                {
                                    "type": "tpl",
                                    "tpl": "关键词：",
                                    "className": "label-text mr-1"
                                },
                                {
                                    "type": "input-text",
                                    "name": "keyword",
                                    "placeholder": "请输入关键词",
                                    "className": "flex-1",
                                    "clearable": True
                                }
                            ]
                        },
                        {
                            "type": "flex",
                            "className": "flex-1 mr-3",
                            "items": [
                                {
                                    "type": "tpl",
                                    "tpl": "品牌：",
                                    "className": "label-text mr-1"
                                },
                                {
                                    "type": "input-text",
                                    "name": "brand",
                                    "placeholder": "请输入品牌",
                                    "className": "flex-1",
                                    "clearable": True
                                }
                            ]
                        },
                        {
                            "type": "flex",
                            "className": "flex-1 mr-3",
                            "items": [
                                {
                                    "type": "tpl",
                                    "tpl": "类目：",
                                    "className": "label-text mr-1"
                                },
                                {
                                    "type": "select",
                                    "name": "category",
                                    "placeholder": "请选择类目",
                                    "className": "flex-1",
                                    "clearable": True,
                                    "searchable": True,
                                    "source": {
                                        "method": "get",
                                        "url": "/api/analysis/categories",
                                        "headers": {
                                            "Authorization": "${ls:access_token ? 'Bearer ' + ls:access_token : ''}"
                                        }
                                    },
                                    "labelField": "label",
                                    "valueField": "value"
                                }
                            ]
                        },
                        {
                            "type": "flex",
                            "className": "flex-1 mr-3",
                            "items": [
                                {
                                    "type": "tpl",
                                    "tpl": "报告日期：",
                                    "className": "label-text mr-1"
                                },
                                {
                                    "type": "input-date",
                                    "name": "report_date",
                                    "format": "YYYY-MM-DD",
                                    "clearable": True,
                                    "className": "flex-1"
                                }
                            ]
                        },
                        # 基础操作按钮 + 上传组件 + 高级搜索按钮
                        {
                            "type": "flex",
                            "className": "flex-none",
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
                                },
                                {
                                    "type": "button",
                                    "label": "高级搜索",
                                    "level": "link",
                                    "size": "sm",
                                    "className": "text-primary",
                                    "style": {
                                        "color": "#007bff !important",
                                        "fontSize": "14px",
                                        "fontWeight": "500"
                                    },
                                    "onEvent": {
                                        "click": {
                                            "actions": [
                                                {
                                                    "actionType": "custom",
                                                    "script": """
                                                        const panel = document.querySelector('.advanced-search-content'); 
                                                        if (panel) { 
                                                            const isHidden = panel.style.display === 'none' || panel.style.display === '';
                                                            panel.style.display = isHidden ? 'block' : 'none'; 

                                                            // 更新按钮文本
                                                            const button = event.target;
                                                            if (button) {
                                                                button.textContent = isHidden ? '收起高级搜索' : '高级搜索';
                                                            }
                                                        }
                                                    """
                                                }
                                            ]
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                },

                # 高级搜索内容面板
                {
                    "type": "container",
                    "className": "advanced-search-content",
                    "style": {
                        "display": "none",
                        "border": "1px solid #e0e0e0",
                        "borderRadius": "4px",
                        "padding": "12px",
                        "backgroundColor": "#f8f9fa",
                        "marginTop": "8px"
                    },
                    "body": [
                        {
                            "type": "tpl",
                            "tpl": "<h6 style='margin: 0 0 12px 0; color: #666; font-weight: 500;'>高级搜索条件</h6>"
                        },
                        SearchComponent._build_additional_search_fields(),
                        SearchComponent._build_ranking_filters(),
                        SearchComponent._build_change_filters(),
                        SearchComponent._build_share_filters(),
                        SearchComponent._build_status_filters()
                    ]
                }
            ]
        }

    @staticmethod
    def _build_additional_search_fields() -> dict:
        """构建额外搜索字段行（ASIN、商品标题）"""
        return {
            "type": "flex",
            "className": "mb-2",
            "items": [
                {
                    "type": "flex",
                    "className": "flex-1 mr-3",
                    "items": [
                        {
                            "type": "tpl",
                            "tpl": "ASIN：",
                            "className": "label-text mr-2"
                        },
                        {
                            "type": "input-text",
                            "name": "asin",
                            "placeholder": "请输入ASIN",
                            "className": "flex-1",
                            "clearable": True
                        }
                    ]
                },
                {
                    "type": "flex",
                    "className": "flex-1 mr-3",
                    "items": [
                        {
                            "type": "tpl",
                            "tpl": "商品标题：",
                            "className": "label-text mr-2"
                        },
                        {
                            "type": "input-text",
                            "name": "product_title",
                            "placeholder": "请输入商品标题",
                            "className": "flex-1",
                            "clearable": True
                        }
                    ]
                },
                {
                    "type": "static",
                    "className": "flex-1 mr-3"
                },
                {
                    "type": "static",
                    "className": "flex-1"
                }
            ]
        }

    @staticmethod
    def _build_ranking_filters() -> dict:
        """构建排名范围搜索"""
        return {
            "type": "flex",
            "className": "mb-2",
            "items": [
                # 日排名范围
                {
                    "type": "flex",
                    "className": "flex-1 mr-3",
                    "items": [
                        {
                            "type": "tpl",
                            "tpl": "日排名：",
                            "className": "label-text mr-2"
                        },
                        {
                            "type": "flex",
                            "className": "range-input-group flex-1",
                            "items": [
                                {
                                    "type": "input-number",
                                    "name": "daily_ranking_min",
                                    "placeholder": "最小值",
                                    "min": 1,
                                    "className": "flex-1"
                                },
                                {
                                    "type": "tpl",
                                    "tpl": "~",
                                    "className": "range-separator px-2"
                                },
                                {
                                    "type": "input-number",
                                    "name": "daily_ranking_max",
                                    "placeholder": "最大值",
                                    "min": 1,
                                    "className": "flex-1"
                                }
                            ]
                        }
                    ]
                },
                # 周排名范围
                {
                    "type": "flex",
                    "className": "flex-1 mr-3",
                    "items": [
                        {
                            "type": "tpl",
                            "tpl": "周排名：",
                            "className": "label-text mr-2"
                        },
                        {
                            "type": "flex",
                            "className": "range-input-group flex-1",
                            "items": [
                                {
                                    "type": "input-number",
                                    "name": "weekly_ranking_min",
                                    "placeholder": "最小值",
                                    "min": 1,
                                    "className": "flex-1"
                                },
                                {
                                    "type": "tpl",
                                    "tpl": "~",
                                    "className": "range-separator px-2"
                                },
                                {
                                    "type": "input-number",
                                    "name": "weekly_ranking_max",
                                    "placeholder": "最大值",
                                    "min": 1,
                                    "className": "flex-1"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "static",
                    "className": "flex-1 mr-3"
                },
                {
                    "type": "static",
                    "className": "flex-1"
                }
            ]
        }

    @staticmethod
    def _build_change_filters() -> dict:
        """构建变化范围搜索"""
        return {
            "type": "flex",
            "className": "mb-2",
            "items": [
                # 日变化范围
                {
                    "type": "flex",
                    "className": "flex-1 mr-3",
                    "items": [
                        {
                            "type": "tpl",
                            "tpl": "日变化：",
                            "className": "label-text mr-2"
                        },
                        {
                            "type": "flex",
                            "className": "range-input-group flex-1",
                            "items": [
                                {
                                    "type": "input-number",
                                    "name": "daily_change_min",
                                    "placeholder": "最小值",
                                    "className": "flex-1"
                                },
                                {
                                    "type": "tpl",
                                    "tpl": "~",
                                    "className": "range-separator px-2"
                                },
                                {
                                    "type": "input-number",
                                    "name": "daily_change_max",
                                    "placeholder": "最大值",
                                    "className": "flex-1"
                                }
                            ]
                        }
                    ]
                },
                # 周变化范围
                {
                    "type": "flex",
                    "className": "flex-1 mr-3",
                    "items": [
                        {
                            "type": "tpl",
                            "tpl": "周变化：",
                            "className": "label-text mr-2"
                        },
                        {
                            "type": "flex",
                            "className": "range-input-group flex-1",
                            "items": [
                                {
                                    "type": "input-number",
                                    "name": "weekly_change_min",
                                    "placeholder": "最小值",
                                    "className": "flex-1"
                                },
                                {
                                    "type": "tpl",
                                    "tpl": "~",
                                    "className": "range-separator px-2"
                                },
                                {
                                    "type": "input-number",
                                    "name": "weekly_change_max",
                                    "placeholder": "最大值",
                                    "className": "flex-1"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "static",
                    "className": "flex-1 mr-3"
                },
                {
                    "type": "static",
                    "className": "flex-1"
                }
            ]
        }

    @staticmethod
    def _build_share_filters() -> dict:
        """构建份额和转化率范围搜索"""
        return {
            "type": "flex",
            "className": "mb-2",
            "items": [
                # 点击份额范围
                {
                    "type": "flex",
                    "className": "flex-1 mr-3",
                    "items": [
                        {
                            "type": "tpl",
                            "tpl": "点击份额(%)：",
                            "className": "label-text mr-2"
                        },
                        {
                            "type": "flex",
                            "className": "range-input-group flex-1",
                            "items": [
                                {
                                    "type": "input-number",
                                    "name": "click_share_min",
                                    "placeholder": "最小值",
                                    "min": 0,
                                    "max": 100,
                                    "precision": 2,
                                    "className": "flex-1"
                                },
                                {
                                    "type": "tpl",
                                    "tpl": "~",
                                    "className": "range-separator px-2"
                                },
                                {
                                    "type": "input-number",
                                    "name": "click_share_max",
                                    "placeholder": "最大值",
                                    "min": 0,
                                    "max": 100,
                                    "precision": 2,
                                    "className": "flex-1"
                                }
                            ]
                        }
                    ]
                },
                # 转化份额范围
                {
                    "type": "flex",
                    "className": "flex-1 mr-3",
                    "items": [
                        {
                            "type": "tpl",
                            "tpl": "转化份额(%)：",
                            "className": "label-text mr-2"
                        },
                        {
                            "type": "flex",
                            "className": "range-input-group flex-1",
                            "items": [
                                {
                                    "type": "input-number",
                                    "name": "conversion_share_min",
                                    "placeholder": "最小值",
                                    "min": 0,
                                    "max": 100,
                                    "precision": 2,
                                    "className": "flex-1"
                                },
                                {
                                    "type": "tpl",
                                    "tpl": "~",
                                    "className": "range-separator px-2"
                                },
                                {
                                    "type": "input-number",
                                    "name": "conversion_share_max",
                                    "placeholder": "最大值",
                                    "min": 0,
                                    "max": 100,
                                    "precision": 2,
                                    "className": "flex-1"
                                }
                            ]
                        }
                    ]
                },
                # 转化率范围
                {
                    "type": "flex",
                    "className": "flex-1",
                    "items": [
                        {
                            "type": "tpl",
                            "tpl": "转化率(%)：",
                            "className": "label-text mr-2"
                        },
                        {
                            "type": "flex",
                            "className": "range-input-group flex-1",
                            "items": [
                                {
                                    "type": "input-number",
                                    "name": "conversion_rate_min",
                                    "placeholder": "最小值",
                                    "min": 0,
                                    "max": 100,
                                    "precision": 2,
                                    "className": "flex-1"
                                },
                                {
                                    "type": "tpl",
                                    "tpl": "~",
                                    "className": "range-separator px-2"
                                },
                                {
                                    "type": "input-number",
                                    "name": "conversion_rate_max",
                                    "placeholder": "最大值",
                                    "min": 0,
                                    "max": 100,
                                    "precision": 2,
                                    "className": "flex-1"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def _build_status_filters() -> dict:
        """构建状态筛选"""
        return {
            "type": "flex",
            "className": "mb-1",
            "items": [
                {
                    "type": "flex",
                    "className": "flex-1 mr-3",
                    "items": [
                        {
                            "type": "tpl",
                            "tpl": "日新品：",
                            "className": "label-text mr-2"
                        },
                        {
                            "type": "select",
                            "name": "is_new_day",
                            "placeholder": "全部",
                            "className": "flex-1",
                            "clearable": True,
                            "options": [
                                {"label": "是", "value": True},
                                {"label": "否", "value": False}
                            ]
                        }
                    ]
                },
                {
                    "type": "flex",
                    "className": "flex-1 mr-3",
                    "items": [
                        {
                            "type": "tpl",
                            "tpl": "周新品：",
                            "className": "label-text mr-2"
                        },
                        {
                            "type": "select",
                            "name": "is_new_week",
                            "placeholder": "全部",
                            "className": "flex-1",
                            "clearable": True,
                            "options": [
                                {"label": "是", "value": True},
                                {"label": "否", "value": False}
                            ]
                        }
                    ]
                },
                {
                    "type": "static",
                    "className": "flex-1 mr-3"
                },
                {
                    "type": "static",
                    "className": "flex-1"
                }
            ]
        }