# ============= app/admin/analysis/upload_component.py =============
"""
上传组件 - 修复文件上传问题的最终版本
针对 fastapi-amis-admin 框架优化
"""
import config


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
        return {
            "title": title,
            "size": "lg",
            "body": {
                "type": "form",
                "encType": "multipart/form-data",
                "api": {
                    "method": "post",
                    "url": "/api/upload/upload-csv",
                    "data": {
                        "file": "${file}",
                        "data_type": data_type
                    }
                },
                "body": [
                    {
                        "type": "input-file",
                        "name": "file",
                        "label": "选择CSV文件",
                        "accept": ".csv",
                        "required": True,
                        "drag": True,
                        "multiple": False,
                        "description": f"请选择{title}的CSV文件，文件大小限制3GB",
                        # 移除可能冲突的配置
                        "autoUpload": False,
                        "useChunk": False,
                        "hideUploadButton": True,
                        # 文件大小限制
                        "maxSize": config.settings.MAX_FILE_SIZE,  # 3GBs
                        "receiver": "/api/upload/upload-csv",
                    },
                    {
                        "type": "hidden",
                        "name": "data_type",
                        "value": data_type
                    },
                    {
                        "type": "divider"
                    },
                    # 关键：状态监控区域
                    {
                        "type": "service",
                        "api": "/api/upload/processing-status",
                        "interval": 5000,
                        "body": {
                            "type": "table",
                            "source": "${items}",
                            "columns": [
                                {"name": "batch_name", "label": "文件名", "width": 200},
                                {"name": "progress_percent", "label": "进度", "type": "progress", "width": 150},
                                {"name": "processing_seconds", "label": "耗时(秒)", "width": 100},
                                {"name": "status", "label": "状态", "width": 100}
                            ],
                            "placeholder": "暂无处理任务"
                        }
                    }
                ]
            },
            "actions": [
                {"type": "button", "label": "取消", "actionType": "cancel"},
                {"type": "submit", "label": "开始上传", "level": "primary", "close": False}
            ]
        }