"""
工具函数包。

提供异常定义、辅助函数等工具模块。
"""

from .exceptions import (
    AppiumMCPError,
    ConfigurationError,
    InvalidConfigError,
    DeviceError,
    DeviceNotFoundError,
    DeviceConnectionError,
    SessionError,
    SessionNotFoundError,
    SessionTimeoutError,
    ToolError,
    ValidationError,
)

from .helpers import (
    generate_session_id,
    generate_element_id,
    validate_device_id,
    get_platform_from_device_id,
    sanitize_filename,
    encode_image_to_base64,
    decode_base64_to_image,
    format_duration,
    format_file_size,
    log_execution_time,
    retry_async,
    timeout_async,
)

__all__ = [
    # 异常类
    "AppiumMCPError",
    "ConfigurationError", 
    "InvalidConfigError",
    "DeviceError",
    "DeviceNotFoundError",
    "DeviceConnectionError",
    "SessionError",
    "SessionNotFoundError",
    "SessionTimeoutError",
    "ToolError",
    "ValidationError",
    # 辅助函数
    "generate_session_id",
    "generate_element_id",
    "validate_device_id",
    "get_platform_from_device_id",
    "sanitize_filename",
    "encode_image_to_base64",
    "decode_base64_to_image",
    "format_duration",
    "format_file_size",
    "log_execution_time",
    "retry_async",
    "timeout_async",
] 