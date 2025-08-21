# app/admin/admin_site.py
from fastapi_amis_admin.admin import AdminSite
from fastapi_amis_admin.admin.site import DocsAdmin, ReDocsAdmin, HomeAdmin, FileAdmin
from config import settings
from fastapi import Request
from fastapi_amis_admin.amis import App
from fastapi_amis_admin.admin.settings import Settings


class CustomAdminSite(AdminSite):
    """自定义管理站点，移除默认的系统信息页面并设置侧边栏默认收起"""

    def __init__(self, settings: Settings):
        super().__init__(settings)
        # 移除默认注册的管理类
        self.unregister_admin(HomeAdmin)  # 这是系统信息页面
        self.unregister_admin(DocsAdmin)  # API文档页面
        self.unregister_admin(ReDocsAdmin)  # ReDoc文档页面


site = CustomAdminSite(
    settings=Settings(
        site_title=settings.APP_NAME,
        site_icon="/static/amazon_logo.png",
        database_url_async=settings.DATABASE_URL_ASYNC,
        site_url="/",
    )
)