# app/admin/admin_site.py
from fastapi_amis_admin.admin import AdminSite
from config import settings
from fastapi_amis_admin.admin.settings import Settings

site = AdminSite(
    settings=Settings(
        site_title=settings.APP_NAME,
        site_icon="/static/amazon_logo.png",
        database_url_async=settings.DATABASE_URL_ASYNC,
        site_url="/",
    )
)