# app/admin/analysis/upload_component.py - 支持分块上传
import config


class UploadComponent:
    """上传功能组件 - 支持分块上传"""

    @staticmethod
    def build_upload_buttons() -> dict:
        """构建上传按钮区域"""
        return {
            "type": "flex",
            "justify": "space-between",
            "items": [
                {"type": "tpl", "tpl": "", "className": "flex-1"},
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
                "headers": {
                    "Authorization": "${ls:access_token ? 'Bearer ' + ls:access_token : ''}"
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
                        "description": f"支持大文件上传，{title}的CSV文件",

                        # 传统上传接口（小文件使用）
                        "receiver": "/api/upload/upload-csv",

                        # AMIS分块上传配置
                        "startChunkApi": {
                            "url": "/api/upload/startChunkApi",
                            "method": "post",
                            "data": {
                                "filename": "${filename}",
                                "filesize": "${size}",
                                "data_type": data_type
                            }
                        },
                        "chunkApi": "/api/upload/chunkApi",
                        "finishChunkApi": "/api/upload/finishChunkApi",

                        # 分块配置 - 符合AMIS规范
                        "chunkSize": 10 * 1024 * 1024,  # 5MB per chunk
                        "useChunk": "auto",  # 让AMIS自动判断是否分块
                        "concurrency": 3,  # 并发上传数量

                        # 上传成功后的处理
                        "onUploaded": "console.log('上传完成:', event.data)"
                    },
                    {
                        "type": "hidden",
                        "name": "data_type",
                        "value": data_type
                    },
                    {"type": "divider"},
                    {
                        "type": "service",
                        "name": "processing_status",
                        "api": f"/api/upload/processing-status?data_type={data_type}",
                        "body": {
                            "type": "table",
                            "source": "${items}",
                            "columns": [
                                {"name": "batch_name", "label": "文件名", "width": 200},
                                {"name": "progress_percent", "label": "进度", "type": "progress", "width": 150},
                                {"name": "total_records", "label": "总记录数", "width": 100},
                                {"name": "status", "label": "状态", "width": 100}
                            ],
                            "placeholder": "暂无处理任务"
                        }
                    }
                ]
            },
            "actions": [
                {"type": "button", "label": "取消", "actionType": "cancel"},
                {"type": "submit", "label": "开始上传", "level": "primary"}
            ]
        }
