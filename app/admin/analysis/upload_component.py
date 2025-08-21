"""
上传组件 - 负责文件上传功能的构建和配置
"""


class UploadComponent:
    """上传功能组件"""

    @staticmethod
    def build_upload_buttons() -> dict:
        """构建上传按钮区域"""
        return {
            "type": "flex",
            "justify": "space-between",
            "items": [
                {
                    "type": "tpl",
                    "tpl": "",  # 占位符，保持布局
                    "className": "flex-1"
                },
                {
                    "type": "flex",
                    "items": [
                        {
                            "type": "button",
                            "label": "上传日数据",
                            "level": "success",
                            "size": "sm",
                            "className": "mr-2",
                            "actionType": "dialog",
                            "dialog": UploadComponent._get_upload_dialog("daily", "上传日数据")
                        },
                        {
                            "type": "button",
                            "label": "上传周数据",
                            "level": "info",
                            "size": "sm",
                            "actionType": "dialog",
                            "dialog": UploadComponent._get_upload_dialog("weekly", "上传周数据")
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def _get_upload_dialog(data_type: str, title: str) -> dict:
        """获取上传对话框配置 - 移除报告日期"""
        return {
            "title": title,
            "size": "md",
            "body": {
                "type": "form",
                "api": {
                    "method": "post",
                    "url": "/api/upload/upload-csv",
                    "messages": {
                        "success": "文件上传成功，正在后台处理数据...",
                        "failed": "文件上传失败，请检查文件格式"
                    }
                },
                "body": [
                    {
                        "type": "alert",
                        "level": "info",
                        "body": f"请选择{title}的CSV文件进行上传。系统将自动解析文件内容并存储到数据库中。",
                        "className": "mb-3"
                    },
                    {
                        "type": "input-file",
                        "name": "file",
                        "label": "选择CSV文件",
                        "accept": ".csv",
                        "required": True,
                        "drag": True,
                        "multiple": False,
                        "description": f"请选择{title}的CSV文件，文件大小限制3GB",
                        "receiver": {
                            "url": "/api/upload/upload-csv"
                        }
                    },
                    {
                        "type": "hidden",
                        "name": "data_type",
                        "value": data_type
                    },
                    {
                        "type": "divider"
                    }
                ],
                "redirect": "/admin/data-analysis",
                "reload": "data_table"
            },
            "actions": [
                {
                    "type": "button",
                    "label": "取消",
                    "actionType": "cancel",
                    "className": "mr-2"
                },
                {
                    "type": "submit",
                    "label": "开始上传",
                    "level": "primary",
                    "className": "upload-submit-btn"
                }
            ]
        }