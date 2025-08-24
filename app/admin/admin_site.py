# app/admin/admin_site.py - 简单修复版本
from fastapi import Request
from fastapi_amis_admin import admin
from fastapi_amis_admin.amis.components import App, Tpl
from fastapi_amis_admin.admin import Settings, AdminSite

from config import settings


class CustomAdminSite(AdminSite):
    """自定义管理站点"""

    async def _get_page_as_app1(self, request: Request) -> App:
        """自定义应用页面"""
        app = App()
        app.brandName = self.site.settings.site_title
        app.logo = self.site.settings.site_icon

        # 添加用户信息和登出功能
        app.header = Tpl(
            className="w-full",
            tpl='''<div class="flex justify-between">
                                   <div class="header-left"></div>
                                   <div class="header-right"></div>
                </div>''',
        )
        app.footer = ''

        children = await self.get_page_schema_children(request)
        app.pages = [{'children': children}] if children else []
        return app


    async def _get_page_as_app(self, request: Request) -> App:
        """自定义应用页面 - 添加认证逻辑"""
        app = App()
        app.brandName = self.site.settings.site_title
        app.logo = self.site.settings.site_icon

        # 添加全局请求拦截器，自动添加Authorization头
        app.requestAdaptor = '''
            const token = localStorage.getItem('access_token');
            if (token && api.url.indexOf('/api/') !== -1) {
                api.headers = api.headers || {};
                api.headers['Authorization'] = 'Bearer ' + token;
            }
            return api;
        '''

        # 添加响应拦截器，处理401错误
        app.responseAdaptor = '''
            if (payload.status === 401) {
                localStorage.removeItem('access_token');
                window.location.href = '/admin/login';
                return payload;
            }
            return payload;
        '''

        # 修复header显示 - 使用正确的amis组件结构
        app.header = {
            "type": "container",
            "className": "w-full bg-white shadow-sm px-4 py-1",
            "body": [
                {
                    "type": "flex",
                    "justify": "space-between",
                    "alignItems": "center",
                    "items": [
                        {
                            "type": "tpl",
                            "tpl": "<h4 class='m-0'>数据分析系统</h4>"
                        },
                        {
                            "type": "button",
                            "label": "退出登录",
                            "level": "link",
                            "size": "sm",
                            "onEvent": {
                                "click": {
                                    "actions": [
                                        {
                                            "actionType": "custom",
                                            "script": """
                                                        localStorage.removeItem('access_token');
                                                        window.location.href = '/admin/login';
                                                    """
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            ]
        }

        app.footer = ''

        children = await self.get_page_schema_children(request)
        app.pages = [{'children': children}] if children else []
        return app

# 初始化站点
site = CustomAdminSite(
    settings=Settings(
        site_title=settings.APP_NAME,
        debug=settings.DEBUG,
        site_icon="/static/amazon_logo.png",
        database_url_async=settings.DATABASE_URL_ASYNC,
        site_url="/",
    )
)

# 取消注册默认管理模块
site.unregister_admin(admin.HomeAdmin)
site.unregister_admin(admin.FileAdmin)

# 注册模块
from app.admin.analysis.analysis_admin import AmazonDataQueryAdmin
from app.admin.user.user_admin import UserManagementAdmin
# from app.admin.auth.login_admin import LoginAdmin

# site.register_admin(LoginAdmin)
site.register_admin(AmazonDataQueryAdmin)
site.register_admin(UserManagementAdmin)
