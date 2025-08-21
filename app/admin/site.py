# app/admin/site.py
from app.admin.admin_site import site  # 从新文件导入 site
from app.admin.analysis_admin import AmazonDataQueryAdmin
from app.admin.user_admin import UserManagementAdmin

# 注册分析模块
site.register_admin(AmazonDataQueryAdmin)
# 注册用户管理模块
site.register_admin(UserManagementAdmin)