# app/admin/user/user_admin.py - 更新版本，添加权限检查
from fastapi import Request, HTTPException, status
from fastapi_amis_admin.admin import admin
from fastapi_amis_admin.amis import PageSchema, Page
from app.admin.admin_site import site


@site.register_admin
class UserManagementAdmin(admin.PageAdmin):
    """用户管理 - 仅超级用户可访问"""
    page_schema = PageSchema(
        label="用户管理",
        icon="fa fa-user",
        sort=10
    )

    async def has_page_permission(self, request: Request, action: str = None) -> bool:
        """检查页面权限 - 仅超级用户"""
        try:
            from app.services.simple_auth import simple_auth
            from database import SessionFactory
            from app.services.login_auth import auth_service
            from app.crud.user_crud import UserCenterCRUD

            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return False

            token = auth_header.split(' ')[1]
            payload = auth_service.decode_access_token(token)
            if not payload:
                return False

            with SessionFactory() as db:
                crud = UserCenterCRUD(db)
                user = crud.get_user_by_username(payload.get('username'))
                return user and user.is_active and user.is_super

        except Exception:
            return False

    async def get_page(self, request: Request) -> Page:
        """构建用户管理页面"""

        # 权限检查 - 没有权限则重定向到登录页面
        if not await self.has_page_permission(request):
            from starlette.responses import RedirectResponse
            return RedirectResponse(url="/admin/login", status_code=302)

        # 搜索表单
        search_form = {
            "type": "form",
            "mode": "horizontal",
            "target": "user_table",
            "className": "m-2",
            "body": [
                {
                    "type": "input-text",
                    "name": "user_name",
                    "label": "用户名:",
                    "placeholder": "请输入用户名",
                    "size": "sm"
                },
                {
                    "type": "select",
                    "name": "is_active",
                    "label": "状态:",
                    "placeholder": "全部",
                    "size": "sm",
                    "options": [
                        {"label": "可用", "value": True},
                        {"label": "禁用", "value": False}
                    ]
                }
            ],
            "actions": [
                {"type": "submit", "label": "搜索", "level": "primary", "size": "sm"},
                {"type": "button", "label": "新增用户", "level": "success", "size": "sm",
                 "actionType": "dialog", "dialog": self._get_create_user_dialog()}
            ]
        }

        # 用户表格
        user_table = {
            "type": "crud",
            "name": "user_table",
            "api": {
                "method": "get",
                "url": "/api/user/list",
                "data": {
                    "page": "${page || 1}",
                    "per_page": "${perPage || 20}",
                    "user_name": "${user_name || ''}",
                    "is_active": "${is_active}"
                }
            },
            "columns": [
                {"name": "id", "label": "ID", "width": 60},
                {"name": "user_name", "label": "用户名", "width": 120},
                {
                    "name": "is_active", "label": "状态", "width": 80,
                    "type": "mapping",
                    "map": {
                        "true": {"type": "status", "value": 1, "label": "可用"},
                        "false": {"type": "status", "value": 0, "label": "禁用"}
                    }
                },
                {
                    "name": "is_super", "label": "超级用户", "width": 100,
                    "type": "mapping",
                    "map": {
                        "true": {"type": "status", "value": 1, "label": "是"},
                        "false": {"type": "status", "value": 0, "label": "否"}
                    }
                },
                {
                    "name": "created_at", "label": "创建时间", "width": 160,
                    "type": "datetime", "format": "YYYY-MM-DD HH:mm:ss"
                },
                {
                    "type": "operation", "label": "操作", "width": 200,
                    "buttons": [
                        {
                            "type": "button", "label": "编辑", "level": "primary", "size": "xs",
                            "actionType": "dialog", "dialog": self._get_edit_user_dialog()
                        },
                        {
                            "type": "button", "label": "切换状态", "level": "warning", "size": "xs",
                            "actionType": "ajax",
                            "api": {"method": "post", "url": "/api/user/toggle-status/${id}"},
                            "confirmText": "确认切换用户状态？"
                        }
                    ]
                }
            ],
            "perPage": 20
        }

        return Page(
            title="用户管理",
            body=[search_form, {"type": "divider"}, user_table]
        )

    def _get_create_user_dialog(self):
        """创建用户对话框"""
        return {
            "title": "新增用户",
            "size": "md",
            "body": {
                "type": "form",
                "api": {"method": "post", "url": "/api/user/create"},
                "body": [
                    {
                        "type": "input-text", "name": "user_name", "label": "用户名",
                        "required": True, "placeholder": "请输入用户名"
                    },
                    {
                        "type": "input-password", "name": "password", "label": "密码",
                        "required": True, "placeholder": "请输入密码"
                    },
                    {
                        "type": "switch", "name": "is_active", "label": "是否激活",
                        "value": True
                    },
                    {
                        "type": "switch", "name": "is_super", "label": "超级管理员",
                        "value": False
                    }
                ]
            },
            "actions": [
                {"type": "button", "label": "取消", "actionType": "cancel"},
                {"type": "submit", "label": "保存", "level": "primary"}
            ]
        }

    def _get_edit_user_dialog(self):
        """编辑用户对话框"""
        return {
            "title": "编辑用户",
            "size": "md",
            "body": {
                "type": "form",
                "initApi": {"method": "get", "url": "/api/user/detail/${id}"},
                "body": [
                    {"type": "static", "name": "id", "label": "用户ID"},
                    {
                        "type": "input-text", "name": "user_name", "label": "用户名",
                        "required": True
                    },
                    {
                        "type": "input-password", "name": "password", "label": "新密码",
                        "placeholder": "不修改请留空"
                    },
                    {"type": "switch", "name": "is_active", "label": "是否激活"},
                    {"type": "switch", "name": "is_super", "label": "超级管理员"}
                ]
            },
            "actions": [
                {"type": "button", "label": "取消", "actionType": "cancel"},
                {
                    "type": "submit", "label": "保存", "level": "primary",
                    "api": {"method": "put", "url": "/api/user/update/${id}"}
                }
            ]
        }