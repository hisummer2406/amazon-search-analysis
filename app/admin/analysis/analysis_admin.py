from fastapi_amis_admin.admin import admin
from fastapi_amis_admin.amis import PageSchema, Page
from app.admin.admin_site import site
from fastapi import Request

# 导入组件
from app.admin.analysis.search_component import SearchComponent
from app.admin.analysis.table_component import TableComponent
from app.admin.analysis.upload_component import UploadComponent


@site.register_admin
class AmazonDataQueryAdmin(admin.PageAdmin):
    """主要数据查询页面 - 组合三个功能组件"""
    page_schema = PageSchema(
        label="数据查询",
        icon="fa fa-search",
        isDefaultPage=True,
        sort=1
    )

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

        # 组合搜索表单和上传按钮
        combined_search_form = self._combine_search_and_upload(search_form, upload_buttons)

        return Page(
            title="数据查询",
            className="analysis-admin",
            body=[
                css_link,
                combined_search_form,
                {"type": "divider"},
                data_table
            ]
        )

    def _combine_search_and_upload(self, search_form: dict, upload_buttons: dict) -> dict:
        """将搜索表单和上传按钮组合到一起 - 适配collapse组件"""
        search_body = search_form.get("body", [])

        # 在collapse组件后添加上传按钮行
        # 找到collapse组件的位置
        collapse_index = -1
        for i, item in enumerate(search_body):
            if item.get("type") == "collapse":
                collapse_index = i
                break

        if collapse_index >= 0:
            # 在collapse组件后插入上传按钮
            upload_row = {
                "type": "flex",
                "justify": "flex-end",  # 右对齐
                "className": "mt-3 mb-3",
                "items": upload_buttons.get("items", [{}])[1].get("items", [])  # 获取上传按钮组
            }
            search_body.insert(collapse_index + 1, upload_row)
        else:
            # 如果没找到collapse组件，就添加到最后
            upload_row = {
                "type": "flex",
                "justify": "flex-end",
                "className": "mt-3 mb-3",
                "items": upload_buttons.get("items", [{}])[1].get("items", [])
            }
            search_body.append(upload_row)

        return search_form