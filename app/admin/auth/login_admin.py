# app/admin/auth/login_admin.py
"""登录页面管理 - 修复路由问题"""
from fastapi import Request
from fastapi_amis_admin.admin import admin
from fastapi_amis_admin.amis import PageSchema, Page
from app.admin.admin_site import site


@site.register_admin
class LoginAdmin(admin.PageAdmin):
    """登录页面"""
    page_schema = PageSchema(
        label="登录",
        icon="fa fa-sign-in",
        sort=1000,
        isDefaultPage=False
    )

    async def get_page(self, request: Request) -> Page:
        return Page(
            title="系统登录",
            body=[
                {
                    "type": "html",
                    "html": """
                    <style>
                        .login-container {
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            min-height: 80vh;
                        }
                        .login-form {
                            width: 400px;
                            padding: 40px;
                            background: white;
                            border-radius: 8px;
                            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                        }
                    </style>
                    """
                },
                {
                    "type": "wrapper",
                    "className": "login-container",
                    "body": [
                        {
                            "type": "form",
                            "title": "用户登录",
                            "className": "login-form",
                            "api": {
                                "method": "post",
                                "url": "/api/auth/login",
                                "adaptor": """
                                if (payload.status === 0) {
                                    // 登录成功，保存token并跳转
                                    localStorage.setItem('access_token', payload.data.access_token);
                                    setTimeout(function() {
                                        window.location.href = '/admin/';
                                    }, 500);
                                    return {
                                        status: 0,
                                        msg: '登录成功，正在跳转...'
                                    };
                                } else {
                                    return {
                                        status: payload.status,
                                        msg: payload.msg
                                    };
                                }
                                """
                            },
                            "body": [
                                {
                                    "type": "html",
                                    "html": """
                                             <div style="text-align: center; margin-bottom: 30px;">
                                                 <img src="/static/amazon_logo.png" alt="Logo" style="height: 60px; margin-bottom: 15px;">
                                                 <h2 style="color: #495057; margin: 0; font-weight: 600;">亚马逊数据分析系统</h2>
                                             </div>
                                             """
                                },
                                {
                                    "type": "input-text",
                                    "name": "username",
                                    "label": "用户名",
                                    "required": True,
                                    "placeholder": "请输入用户名"
                                },
                                {
                                    "type": "input-password",
                                    "name": "password",
                                    "label": "密码",
                                    "required": True,
                                    "placeholder": "请输入密码"
                                }
                            ],
                            "actions": [
                                {
                                    "type": "submit",
                                    "label": "登录",
                                    "level": "primary",
                                    "size": "lg"
                                }
                            ]
                        }
                    ]
                }
            ]
        )
