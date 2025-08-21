"""
组件模块初始化文件

包含三个功能组件：
- SearchComponent: 搜索功能组件
- TableComponent: 表格显示组件
- UploadComponent: 上传功能组件

这些组件被主页面 analysis_admin.py 组合使用
"""

from .search_component import SearchComponent
from .table_component import TableComponent
from .upload_component import UploadComponent

__all__ = [
    'SearchComponent',
    'TableComponent',
    'UploadComponent'
]