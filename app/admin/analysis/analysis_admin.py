from fastapi_amis_admin.admin import admin
from fastapi_amis_admin.amis import PageSchema, Page
from fastapi_amis_admin.amis.components import App, Tpl

from app.admin.admin_site import site
from fastapi import Request

# 导入组件
from app.admin.analysis.search_component import SearchComponent
from app.admin.analysis.table_component import TableComponent
from app.admin.analysis.upload_component import UploadComponent


@site.register_admin
class AmazonDataQueryAdmin(admin.PageAdmin):
    """主要数据查询页面 - 组合三个功能组件"""
    page_path = '/analysis'
    router_prefix = ''
    page_schema = PageSchema(
        label="数据查询",
        icon="fa fa-search",
        isDefaultPage=True,
        sort=1
    )

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

        # 添加用户信息和登出功能
        app.header = Tpl(
            className="w-full",
            tpl='''<div class="flex justify-between">
                       <div class="header-left"></div>
                       <div class="header-right">
                           <button onclick="logout()" class="btn btn-sm">登出</button>
                       </div>
                    </div>
                    <script>
                    function logout() {
                        localStorage.removeItem('access_token');
                        window.location.href = '/admin/login';
                    }
                    </script>''',
        )

        children = await self.get_page_schema_children(request)
        app.pages = [{'children': children}] if children else []
        return app

    async def get_page(self, request: Request) -> Page:
        # 引入外部CSS样式
        css_link = {
            "type": "html",
            "html": '<link rel="stylesheet" href="/static/analysis_admin.css">'
        }

        # 构建各个功能组件
        search_form = SearchComponent.build_search_form()
        upload_buttons = UploadComponent.build_upload_buttons()
        data_table = TableComponent.build_data_table()

        # 简化布局：直接修改第一行按钮组
        self._add_upload_to_first_row(search_form, upload_buttons)

        return Page(
            title="数据查询",
            className="analysis-admin",
            body=[
                css_link,
                search_form,
                {"type": "divider"},
                data_table
            ]
        )

    def _add_upload_to_first_row(self, search_form: dict, upload_buttons: dict) -> None:
        """将上传按钮添加到第一行"""
        # 获取上传按钮
        upload_items = upload_buttons["items"][1]["items"]

        # 找到第一行的按钮组并添加上传按钮
        first_row = search_form["body"][0]["items"]
        button_group = first_row[-1]["items"]
        button_group.extend(upload_items)
