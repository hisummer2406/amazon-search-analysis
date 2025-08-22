"""
搜索组件 - 优化第一行布局，标签和输入框在同一行
"""


class SearchComponent:
    """搜索功能组件"""

    @staticmethod
    def build_search_form() -> dict:
        """构建搜索表单 - 优化第一行布局"""
        return {
            "type": "form",
            "target": "data_table",
            "className": "search-form",
            "wrapWithPanel": False,
            "body": [
                # 第一行：基础搜索条件 - 使用flex布局，标签和输入框左右排列
                {
                    "type": "flex",
                    "className": "mb-3",
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
                                    "className": "flex-1"
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
                                    "className": "flex-1"
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
                                    "type": "input-text",
                                    "name": "category",
                                    "placeholder": "请输入类目",
                                    "className": "flex-1"
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
                        # 基础操作按钮
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
                                }
                            ]
                        }
                    ]
                },

                # 高级搜索 - 使用 collapse 组件
                {
                    "type": "collapse",
                    "header": "高级搜索",
                    "collapsed": True,
                    "className": "mb-3",
                    "body": [
                        # 新品筛选行
                        {
                            "type": "flex",
                            "className": "mb-3",
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
                        },

                        # 排名和变化范围搜索
                        {
                            "type": "flex",
                            "className": "mb-3",
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
                                                    "min": 1
                                                },
                                                {
                                                    "type": "tpl",
                                                    "tpl": "~",
                                                    "className": "range-separator"
                                                },
                                                {
                                                    "type": "input-number",
                                                    "name": "daily_ranking_max",
                                                    "placeholder": "最大值",
                                                    "min": 1
                                                }
                                            ]
                                        }
                                    ]
                                },
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
                                                    "placeholder": "最小值"
                                                },
                                                {
                                                    "type": "tpl",
                                                    "tpl": "~",
                                                    "className": "range-separator"
                                                },
                                                {
                                                    "type": "input-number",
                                                    "name": "daily_change_max",
                                                    "placeholder": "最大值"
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
                                                    "min": 1
                                                },
                                                {
                                                    "type": "tpl",
                                                    "tpl": "~",
                                                    "className": "range-separator"
                                                },
                                                {
                                                    "type": "input-number",
                                                    "name": "weekly_ranking_max",
                                                    "placeholder": "最大值",
                                                    "min": 1
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # 周变化范围
                                {
                                    "type": "flex",
                                    "className": "flex-1",
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
                                                    "placeholder": "最小值"
                                                },
                                                {
                                                    "type": "tpl",
                                                    "tpl": "~",
                                                    "className": "range-separator"
                                                },
                                                {
                                                    "type": "input-number",
                                                    "name": "weekly_change_max",
                                                    "placeholder": "最大值"
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },

                        # 份额和转化率范围搜索
                        {
                            "type": "flex",
                            "className": "mb-3",
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
                                                    "precision": 2
                                                },
                                                {
                                                    "type": "tpl",
                                                    "tpl": "~",
                                                    "className": "range-separator"
                                                },
                                                {
                                                    "type": "input-number",
                                                    "name": "click_share_max",
                                                    "placeholder": "最大值",
                                                    "min": 0,
                                                    "max": 100,
                                                    "precision": 2
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
                                                    "precision": 2
                                                },
                                                {
                                                    "type": "tpl",
                                                    "tpl": "~",
                                                    "className": "range-separator"
                                                },
                                                {
                                                    "type": "input-number",
                                                    "name": "conversion_share_max",
                                                    "placeholder": "最大值",
                                                    "min": 0,
                                                    "max": 100,
                                                    "precision": 2
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
                                                    "precision": 2
                                                },
                                                {
                                                    "type": "tpl",
                                                    "tpl": "~",
                                                    "className": "range-separator"
                                                },
                                                {
                                                    "type": "input-number",
                                                    "name": "conversion_rate_max",
                                                    "placeholder": "最大值",
                                                    "min": 0,
                                                    "max": 100,
                                                    "precision": 2
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }