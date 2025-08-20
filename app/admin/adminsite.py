from fastapi_amis_admin.admin import AdminSite, Settings

site = AdminSite(
    settings=Settings(
        site_title='Amazon 搜索分析',
        database_url_async='sqlite:///amisadmin.db',
    )
)