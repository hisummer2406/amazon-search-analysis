from typing import Optional, Union


def safe_int(value: Union[str, int, None], default: int = 1) -> int:
    """安全地将值转换为整数"""
    if value is None or value == "":
        return default

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    return default


def safe_bool(value: Union[str, bool, None]) -> Optional[bool]:
    """安全地将值转换为布尔值"""
    if value is None or value == "":
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower in ['true', '1', 'yes', 'on']:
            return True
        elif value_lower in ['false', '0', 'no', 'off']:
            return False
        else:
            return None

    return None


def safe_str(value: Union[str, None]) -> Optional[str]:
    """安全地处理字符串值"""
    if value is None or value == "":
        return None

    if isinstance(value, str):
        value = value.strip()
        return value if value else None

    return str(value) if value else None