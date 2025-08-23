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
        """获取上传对话框配置 - 最终修复版本"""
        return {
            "title": title,
            "size": "lg",
            "body": {
                "type": "form",
                # 关键修复2: 明确设置表单编码
                "encType": "multipart/form-data",
                "body": [
                    # 文件上传区域
                    {
                        "type": "fieldset",
                        "title": "文件上传",
                        "className": "mb-4",
                        "body": [
                            {
                                "type": "alert",
                                "level": "info",
                                "body": f"请选择{title}的CSV文件进行上传。系统将自动解析文件内容并存储到数据库中。",
                                "className": "mb-3"
                            },
                            # 关键修复3: 简化input-file配置
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
                            }
                        ]
                    },
                    # 处理状态显示区域
                    UploadComponent._build_status_section(),
                    {
                        "type": "divider"
                    },
                ],
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
                    "className": "upload-submit-btn",
                    "close": False
                }
            ]
        }

    @staticmethod
    def _build_status_section() -> dict:
        """构建处理状态显示区域"""
        return {
            "type": "service",
            "api": {
                "method": "get",
                "url": "/api/upload/processing-status"
            },
            "interval": 5000,  # 每5秒刷新一次
            "body": {
                "type": "container",
                "visibleOn": "${items && items.length > 0}",
                "body": [
                    {
                        "type": "fieldset",
                        "title": "正在处理的任务",
                        "className": "mt-4",
                        "body": [
                            {
                                "type": "table",
                                "source": "${items}",
                                "className": "table-sm",
                                "columns": [
                                    {
                                        "name": "batch_name",
                                        "label": "文件名",
                                        "type": "text"
                                    },
                                    {
                                        "name": "data_type_display",
                                        "label": "类型",
                                        "type": "tpl",
                                        "tpl": "${is_day_data ? '日数据' : '周数据'}",
                                        "width": 80
                                    },
                                    {
                                        "name": "progress_percent",
                                        "label": "进度",
                                        "type": "tpl",
                                        "width": 150,
                                        "tpl": '''
                                        <div class="flex items-center">
                                            <div class="w-full bg-gray-200 rounded-full h-2 mr-2">
                                                <div class="bg-blue-600 h-2 rounded-full" style="width: ${progress_percent}%"></div>
                                            </div>
                                            <span class="text-xs">${progress_percent}%</span>
                                        </div>
                                        '''
                                    },
                                    {
                                        "name": "processed_info",
                                        "label": "处理信息",
                                        "type": "tpl",
                                        "tpl": "${processed_keywords}/${total_records} 条"
                                    },
                                    {
                                        "name": "processing_time",
                                        "label": "耗时",
                                        "type": "tpl",
                                        "tpl": "${processing_seconds}秒",
                                        "width": 80
                                    },
                                    {
                                        "name": "status_display",
                                        "label": "状态",
                                        "type": "tpl",
                                        "width": 80,
                                        "tpl": '''
                                        <span class="${status === 'PROCESSING' ? 'text-blue-600' : status === 'COMPLETED' ? 'text-green-600' : 'text-red-600'}">
                                            ${status === 'PROCESSING' ? '处理中' : status === 'COMPLETED' ? '已完成' : '失败'}
                                        </span>
                                        '''
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }


# ============= 调试版本：添加测试按钮 =============
class DebugUploadComponent(UploadComponent):
    """调试版本的上传组件，包含测试功能"""

    @staticmethod
    def _get_test_upload_dialog() -> dict:
        """测试上传对话框"""
        return {
            "title": "测试文件上传",
            "size": "md",
            "body": {
                "type": "form",
                "encType": "multipart/form-data",
                "body": [
                    {
                        "type": "alert",
                        "level": "warning",
                        "body": "这是测试功能，仅用于验证文件上传是否正常工作。",
                        "className": "mb-3"
                    },
                    {
                        "type": "input-file",
                        "name": "file",
                        "label": "选择任意文件",
                        "required": True,
                        "accept": ".csv",
                        "maxSize": config.settings.MAX_FILE_SIZE,
                        "receiver": "/api/upload/test-upload",
                        "autoUpload": False,
                        "hideUploadButton": True,
                    },
                    {
                        "type": "input-text",
                        "name": "test_param",
                        "label": "测试参数",
                        "value": "test_value"
                    }
                ]
            },
            "actions": [
                {
                    "type": "button",
                    "label": "取消",
                    "actionType": "cancel"
                },
                {
                    "type": "submit",
                    "label": "测试上传",
                    "level": "primary"
                }
            ]
        }

    @staticmethod
    def build_upload_buttons() -> dict:
        """构建上传按钮区域 - 包含调试功能"""
        base_buttons = UploadComponent.build_upload_buttons()

        # 添加测试按钮
        test_button = {
            "type": "button",
            "label": "测试上传",
            "level": "warning",
            "size": "sm",
            "className": "ml-2",
            "actionType": "dialog",
            "dialog": DebugUploadComponent._get_test_upload_dialog()
        }

        base_buttons["items"][1]["items"].append(test_button)
        return base_buttons
