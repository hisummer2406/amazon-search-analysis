# app/admin/admin_site.py - 简单修复版本
from fastapi import Request
from fastapi_amis_admin import admin
from fastapi_amis_admin.amis.components import App, Tpl
from fastapi_amis_admin.admin import Settings, AdminSite

from config import settings


class CustomAdminSite(AdminSite):
    """自定义管理站点"""

    async def _get_page_as_app(self, request: Request) -> App:
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
