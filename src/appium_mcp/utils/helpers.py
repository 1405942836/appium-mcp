"""
工具函数模块。

提供Appium MCP服务器使用的各种工具函数和辅助方法。
"""

import asyncio
import base64
import json
import re
import time
import uuid
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import structlog
from PIL import Image

from .exceptions import ValidationError

logger = structlog.get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def generate_session_id() -> str:
    """生成唯一的会话ID。"""
    return str(uuid.uuid4())


def generate_element_id() -> str:
    """生成唯一的元素ID。"""
    return f"element-{uuid.uuid4().hex[:8]}"


def validate_device_id(device_id: str) -> bool:
    """
    验证设备ID格式。

    Args:
        device_id: 设备ID

    Returns:
        是否为有效的设备ID
    """
    if not device_id or not isinstance(device_id, str):
        return False

    # Android模拟器格式: emulator-5554
    # Android真机格式: 通常是字母数字组合
    # iOS模拟器格式: 通常是UUID格式
    patterns = [
        r"^emulator-\d+$",  # Android模拟器
        r"^[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}$",  # UUID格式
        r"^[A-Za-z0-9]+$",  # 一般格式
    ]

    return any(re.match(pattern, device_id) for pattern in patterns)


def validate_app_package(package: str, platform: str = "android") -> bool:
    """
    验证应用包名格式。

    Args:
        package: 包名
        platform: 平台类型

    Returns:
        是否为有效的包名
    """
    if not package or not isinstance(package, str):
        return False

    if platform.lower() == "android":
        # Android包名格式: com.example.app
        pattern = r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$"
        return bool(re.match(pattern, package))
    elif platform.lower() == "ios":
        # iOS Bundle ID格式: com.example.app
        pattern = r"^[a-zA-Z][a-zA-Z0-9_-]*(\.[a-zA-Z][a-zA-Z0-9_-]*)+$"
        return bool(re.match(pattern, package))

    return False


def validate_coordinates(x: Union[int, float], y: Union[int, float]) -> bool:
    """
    验证坐标值。

    Args:
        x: X坐标
        y: Y坐标

    Returns:
        坐标是否有效
    """
    try:
        x_val = float(x)
        y_val = float(y)
        return x_val >= 0 and y_val >= 0
    except (TypeError, ValueError):
        return False


def parse_locator(locator_type: str, locator_value: str) -> Dict[str, str]:
    """
    解析定位器。

    Args:
        locator_type: 定位器类型
        locator_value: 定位器值

    Returns:
        解析后的定位器字典

    Raises:
        ValidationError: 定位器无效
    """
    valid_locator_types = [
        "id",
        "name",
        "class_name",
        "tag_name",
        "xpath",
        "css_selector",
        "accessibility_id",
        "android_uiautomator",
        "ios_predicate",
        "ios_class_chain",
    ]

    if locator_type not in valid_locator_types:
        raise ValidationError(
            f"Invalid locator type: {locator_type}",
            "locator_type",
            locator_type,
            {"valid_types": valid_locator_types},
        )

    if not locator_value or not isinstance(locator_value, str):
        raise ValidationError(
            "Locator value cannot be empty",
            "locator_value",
            locator_value,
        )

    return {"type": locator_type, "value": locator_value}


def format_duration(seconds: Union[int, float]) -> str:
    """
    格式化持续时间。

    Args:
        seconds: 秒数

    Returns:
        格式化的时间字符串
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:.0f}m {secs:.0f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h {minutes:.0f}m"


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小。

    Args:
        size_bytes: 字节数

    Returns:
        格式化的文件大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f}KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / (1024**2):.1f}MB"
    else:
        return f"{size_bytes / (1024**3):.1f}GB"


def encode_image_to_base64(image_path: Union[str, Path]) -> str:
    """
    将图片编码为base64字符串。

    Args:
        image_path: 图片路径

    Returns:
        base64编码的图片字符串

    Raises:
        FileNotFoundError: 文件不存在
        ValidationError: 文件格式不支持
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        return base64.b64encode(image_data).decode("utf-8")
    except Exception as e:
        raise ValidationError(f"Failed to encode image: {e}", "image_path", str(image_path))


def decode_base64_to_image(base64_data: str, output_path: Union[str, Path]) -> None:
    """
    将base64字符串解码为图片文件。

    Args:
        base64_data: base64编码的图片数据
        output_path: 输出文件路径

    Raises:
        ValidationError: 解码失败
    """
    try:
        image_data = base64.b64decode(base64_data)
        with open(output_path, "wb") as f:
            f.write(image_data)
    except Exception as e:
        raise ValidationError(f"Failed to decode image: {e}", "base64_data", base64_data)


def resize_image(
    image_path: Union[str, Path],
    output_path: Union[str, Path],
    max_width: int = 1920,
    max_height: int = 1080,
    quality: int = 85,
) -> None:
    """
    调整图片大小。

    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径
        max_width: 最大宽度
        max_height: 最大高度
        quality: 图片质量 (1-100)

    Raises:
        ValidationError: 图片处理失败
    """
    try:
        with Image.open(image_path) as img:
            # 计算新尺寸
            width, height = img.size
            ratio = min(max_width / width, max_height / height)

            if ratio < 1:
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 保存图片
            img.save(output_path, optimize=True, quality=quality)

    except Exception as e:
        raise ValidationError(f"Failed to resize image: {e}", "image_path", str(image_path))


def retry_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """
    异步重试装饰器。

    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数
        exceptions: 需要重试的异常类型

    Returns:
        装饰器函数
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            "Function failed, retrying",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                            delay=current_delay,
                            error=str(e),
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "Function failed after all retries",
                            function=func.__name__,
                            max_attempts=max_attempts,
                            error=str(e),
                        )

            raise last_exception

        return wrapper

    return decorator


def timeout_async(timeout_seconds: float) -> Callable[[F], F]:
    """
    异步超时装饰器。

    Args:
        timeout_seconds: 超时时间（秒）

    Returns:
        装饰器函数
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.error(
                    "Function timed out",
                    function=func.__name__,
                    timeout=timeout_seconds,
                )
                raise

        return wrapper

    return decorator


def log_execution_time(func: F) -> F:
    """
    记录函数执行时间的装饰器。

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                "Function executed successfully",
                function=func.__name__,
                execution_time=format_duration(execution_time),
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "Function execution failed",
                function=func.__name__,
                execution_time=format_duration(execution_time),
                error=str(e),
            )
            raise

    return wrapper


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符。

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(illegal_chars, "_", filename)

    # 移除连续的下划线
    sanitized = re.sub(r"_+", "_", sanitized)

    # 移除开头和结尾的下划线和空格
    sanitized = sanitized.strip("_ ")

    # 确保文件名不为空
    if not sanitized:
        sanitized = "unnamed_file"

    return sanitized


def parse_json_safely(json_str: str) -> Optional[Dict[str, Any]]:
    """
    安全地解析JSON字符串。

    Args:
        json_str: JSON字符串

    Returns:
        解析后的字典，解析失败返回None
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度合并两个字典。

    Args:
        dict1: 第一个字典
        dict2: 第二个字典

    Returns:
        合并后的字典
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    扁平化嵌套字典。

    Args:
        d: 要扁平化的字典
        parent_key: 父键名
        sep: 分隔符

    Returns:
        扁平化后的字典
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_platform_from_device_id(device_id: str) -> Optional[str]:
    """
    从设备ID推断平台类型。

    Args:
        device_id: 设备ID

    Returns:
        平台类型 ("android" 或 "ios")，无法推断返回None
    """
    if device_id.startswith("emulator-") or re.match(r"^[A-Za-z0-9]{16}$", device_id):
        return "android"
    elif re.match(r"^[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}$", device_id):
        return "ios"
    else:
        return None


def create_capability_dict(
    platform: str,
    device_id: str,
    app_package: Optional[str] = None,
    app_activity: Optional[str] = None,
    bundle_id: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    创建Appium能力字典。

    Args:
        platform: 平台类型
        device_id: 设备ID
        app_package: Android应用包名
        app_activity: Android应用Activity
        bundle_id: iOS Bundle ID
        **kwargs: 其他能力参数

    Returns:
        能力字典
    """
    capabilities = {
        "platformName": platform.title(),
        "deviceName": device_id,
        "udid": device_id,
    }

    if platform.lower() == "android":
        capabilities["automationName"] = "UiAutomator2"
        if app_package:
            capabilities["appPackage"] = app_package
        if app_activity:
            capabilities["appActivity"] = app_activity
    elif platform.lower() == "ios":
        capabilities["automationName"] = "XCUITest"
        if bundle_id:
            capabilities["bundleId"] = bundle_id

    # 添加其他参数
    capabilities.update(kwargs)

    return capabilities 