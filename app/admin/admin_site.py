# app/admin/admin_site.py
from fastapi_amis_admin.amis.components import App, Tpl, Page
from fastapi_user_auth.admin import AuthAdminSite
from config import settings
from fastapi_amis_admin.admin import AdminSite, PageSchemaAdmin, Settings
from fastapi_amis_admin.amis.constants import SizeEnum
from fastapi_amis_admin.amis.types import AmisAPI
from fastapi_amis_admin.utils.translation import i18n as _
from starlette.requests import Request
from fastapi_user_auth.auth.schemas import SystemUserEnum

from fastapi_amis_admin.amis.components import (
    ActionType,
    App,
    Dialog,
    Flex,
    Service,
)

class CustomAdminSite(AdminSite):

    async def _get_page_as_app(self, request: Request) -> App:
        app = App()
        app.brandName = self.site.settings.site_title
        app.logo = self.site.settings.site_icon
        app.header = Tpl(
            className="w-full",
            tpl='''<div class="flex justify-between">
                        <div class="header-left"></div>
                        <div class="header-right">
                            <i class="fa fa-github fa-2x" aria-label="GitHub 仓库"></i>
                        </div>
                   </div>''',
        )
        app.footer = ('')
        children = await self.get_page_schema_children(request)
        app.pages = [{'children': children}] if children else []
        return app

# 正确初始化站点设置
site = CustomAdminSite(
    settings=Settings(
        site_title=settings.APP_NAME,
        debug=settings.DEBUG,
        site_icon="/static/amazon_logo.png",
        database_url_async=settings.DATABASE_URL_ASYNC,
        site_url="/",
    )
)
