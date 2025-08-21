# app/admin/user_admin.py
from fastapi_amis_admin.admin import admin
from fastapi_amis_admin.amis import PageSchema, Page, Dialog, Form, Button
from app.admin.admin_site import site
from fastapi import Request


@site.register_admin  # 使用新的 site 实例
class UserManagementAdmin(admin.PageAdmin):
    """用户管理"""
    page_schema = PageSchema(label="用户管理", icon="fa fa-user")

    async def get_page(self, request: Request) -> Page:
        """构建用户管理页面"""

        # 顶部搜索和操作区域
        header_toolbar = {
            "type": "form",
            "mode": "horizontal",
            "target": "user_table",
            "className": "m-2",
            "body": [
                {
                    "type": "group",
                    "body": [
                        {
                            "type": "input-text",
                            "name": "user_name",
                            "label": "搜索用户:",
                            "placeholder": "请输入用户名",
                            "size": "sm",
                            "className": "w-60"
                        },
                        {
                            "type": "select",
                            "name": "is_active",
                            "label": "用户状态:",
                            "placeholder": "全部",
                            "size": "sm",
                            "className": "min-w-[160px] z-50",
                            "options": [
                                {"label": "全部", "value": ""},
                                {"label": "激活", "value": True},
                                {"label": "禁用", "value": False}
                            ],
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "submit",
                    "label": "搜索",
                    "level": "primary",
                    "size": "sm"
                },
                {
                    "type": "button",
                    "label": "新增用户",
                    "level": "success",
                    "size": "sm",
                    "actionType": "dialog",
                    "dialog": self._get_create_user_dialog()
                }
            ]
        }

        # 用户列表表格
        user_table = {
            "type": "service",
            "name": "user_table",
            "api": {
                "method": "get",
                "url": "/api/user/list",
                "data": {
                    "page": "${page}",
                    "per_page": "${perPage}",
                    "user_name": "${user_name}",
                    "is_active": "${is_active}"
                }
            },
            "body": {
                "type": "table",
                "source": "${data.items}",
                "columns": [
                    {
                        "name": "id",
                        "label": "ID",
                        "width": 60,
                        "type": "text"
                    },
                    {
                        "name": "user_name",
                        "label": "用户名",
                        "type": "text",
                        "width": 120
                    },
                    {
                        "name": "is_active",
                        "label": "状态",
                        "type": "mapping",
                        "width": 80,
                        "map": {
                            "True": {"type": "status", "value": 1, "label": "激活"},
                            "False": {"type": "status", "value": 0, "label": "禁用"}
                        }
                    },
                    {
                        "name": "created_at",
                        "label": "创建时间",
                        "type": "datetime",
                        "width": 160,
                        "format": "YYYY-MM-DD HH:mm:ss"
                    },
                    {
                        "type": "operation",
                        "label": "操作",
                        "width": 200,
                        "buttons": [
                            {
                                "type": "button",
                                "label": "编辑",
                                "level": "primary",
                                "size": "xs",
                                "actionType": "dialog",
                                "dialog": self._get_edit_user_dialog()
                            },
                            {
                                "type": "button",
                                "label": "切换状态",
                                "level": "warning",
                                "size": "xs",
                                "actionType": "ajax",
                                "api": {
                                    "method": "post",
                                    "url": "/api/user/toggle-status/${id}"
                                },
                                "confirmText": "确认切换用户状态？"
                            }
                        ]
                    }
                ],
                # 分页配置
                "pagination": {
                    "perPage": 20,
                    "perPageAvailable": [10, 20, 50, 100],
                    "showPerPage": True,
                    "showPageInput": True
                },
                # 表格配置
                "headerToolbar": [
                    "pagination",
                    {
                        "type": "tpl",
                        "tpl": "共 ${data.count} 条记录",
                        "className": "text-muted"
                    }
                ],
                "footerToolbar": ["pagination"]
            }
        }

        return Page(
            title="用户管理",
            body=[
                header_toolbar,
                {"type": "divider"},
                user_table
            ]
        )

    def _get_create_user_dialog(self) -> Dialog:
        """创建用户对话框"""
        return {
            "title": "新增用户",
            "size": "md",
            "body": {
                "type": "form",
                "api": {
                    "method": "post",
                    "url": "/api/user/create"
                },
                "body": [
                    {
                        "type": "input-text",
                        "name": "user_name",
                        "label": "用户名",
                        "required": True,
                        "placeholder": "请输入用户名（3-50个字符）",
                        "validations": {
                            "minLength": 3,
                            "maxLength": 50,
                            "matchRegexp": "^[a-zA-Z0-9]+$"
                        },
                        "validationErrors": {
                            "minLength": "用户名至少3个字符",
                            "maxLength": "用户名最多50个字符",
                            "matchRegexp": "用户名只能包含字母和数字"
                        }
                    },
                    {
                        "type": "input-password",
                        "name": "password",
                        "label": "密码",
                        "required": True,
                        "placeholder": "请输入密码（至少6位）",
                        "validations": {
                            "minLength": 6
                        },
                        "validationErrors": {
                            "minLength": "密码至少6位"
                        }
                    },
                    {
                        "type": "input-password",
                        "name": "confirm_password",
                        "label": "确认密码",
                        "required": True,
                        "placeholder": "请再次输入密码",
                        "validations": {
                            "equalsField": "password"
                        },
                        "validationErrors": {
                            "equalsField": "两次输入的密码不一致"
                        }
                    },
                    {
                        "type": "switch",
                        "name": "is_active",
                        "label": "是否激活",
                        "value": True,
                        "trueValue": True,
                        "falseValue": False
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
                    "label": "保存",
                    "level": "primary"
                }
            ]
        }

    def _get_edit_user_dialog(self) -> Dialog:
        """编辑用户对话框"""
        return {
            "title": "编辑用户",
            "size": "md",
            "body": {
                "type": "form",
                "api": {
                    "method": "get",
                    "url": "/api/user/detail/${id}",
                    "dataType": "json"
                },
                "initApi": {
                    "method": "get",
                    "url": "/api/user/detail/${id}"
                },
                "body": [
                    {
                        "type": "static",
                        "name": "id",
                        "label": "用户ID"
                    },
                    {
                        "type": "input-text",
                        "name": "user_name",
                        "label": "用户名",
                        "required": True,
                        "validations": {
                            "minLength": 3,
                            "maxLength": 50,
                            "matchRegexp": "^[a-zA-Z0-9]+$"
                        },
                        "validationErrors": {
                            "minLength": "用户名至少3个字符",
                            "maxLength": "用户名最多50个字符",
                            "matchRegexp": "用户名只能包含字母和数字"
                        }
                    },
                    {
                        "type": "input-password",
                        "name": "password",
                        "label": "新密码",
                        "placeholder": "不修改请留空",
                        "validations": {
                            "minLength": 6
                        },
                        "validationErrors": {
                            "minLength": "密码至少6位"
                        }
                    },
                    {
                        "type": "switch",
                        "name": "is_active",
                        "label": "是否激活",
                        "trueValue": True,
                        "falseValue": False
                    },
                    {
                        "type": "switch",
                        "name": "is_super",
                        "label": "超级管理员",
                        "trueValue": True,
                        "falseValue": False,
                        "description": "超级管理员拥有所有权限"
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
                    "label": "保存",
                    "level": "primary",
                    "api": {
                        "method": "put",
                        "url": "/api/user/update/${id}"
                    }
                }
            ]
        }
