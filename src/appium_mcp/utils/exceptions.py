"""
自定义异常类定义。

定义了Appium MCP服务器使用的所有自定义异常类，
提供更精确的错误处理和用户反馈。
"""

from typing import Any, Dict, Optional


class AppiumMCPError(Exception):
    """Appium MCP服务器基础异常类。"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化异常。

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 额外的错误详情
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "APPIUM_MCP_ERROR"
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """将异常转换为字典格式。"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class DeviceError(AppiumMCPError):
    """设备相关错误。"""

    def __init__(
        self,
        message: str,
        device_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "DEVICE_ERROR", details)
        self.device_id = device_id


class DeviceNotFoundError(DeviceError):
    """设备未找到错误。"""

    def __init__(self, device_id: str) -> None:
        super().__init__(
            f"Device not found: {device_id}",
            device_id,
            {"error_code": "DEVICE_NOT_FOUND"},
        )


class DeviceConnectionError(DeviceError):
    """设备连接错误。"""

    def __init__(self, device_id: str, reason: str) -> None:
        super().__init__(
            f"Failed to connect to device {device_id}: {reason}",
            device_id,
            {"error_code": "DEVICE_CONNECTION_ERROR", "reason": reason},
        )


class SessionError(AppiumMCPError):
    """会话相关错误。"""

    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "SESSION_ERROR", details)
        self.session_id = session_id


class SessionNotFoundError(SessionError):
    """会话未找到错误。"""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            f"Session not found: {session_id}",
            session_id,
            {"error_code": "SESSION_NOT_FOUND"},
        )


class SessionTimeoutError(SessionError):
    """会话超时错误。"""

    def __init__(self, session_id: str, timeout: int) -> None:
        super().__init__(
            f"Session {session_id} timed out after {timeout} seconds",
            session_id,
            {"error_code": "SESSION_TIMEOUT", "timeout": timeout},
        )


class ElementError(AppiumMCPError):
    """元素相关错误。"""

    def __init__(
        self,
        message: str,
        element_id: Optional[str] = None,
        locator: Optional[Dict[str, str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "ELEMENT_ERROR", details)
        self.element_id = element_id
        self.locator = locator


class ElementNotFoundError(ElementError):
    """元素未找到错误。"""

    def __init__(self, locator: Dict[str, str]) -> None:
        super().__init__(
            f"Element not found with locator: {locator}",
            locator=locator,
            details={"error_code": "ELEMENT_NOT_FOUND", "locator": locator},
        )


class ElementNotInteractableError(ElementError):
    """元素不可交互错误。"""

    def __init__(self, element_id: str, reason: str = "") -> None:
        super().__init__(
            f"Element {element_id} is not interactable. {reason}".strip(),
            element_id,
            {"error_code": "ELEMENT_NOT_INTERACTABLE", "reason": reason},
        )


class AppError(AppiumMCPError):
    """应用相关错误。"""

    def __init__(
        self,
        message: str,
        app_package: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "APP_ERROR", details)
        self.app_package = app_package


class AppNotInstalledError(AppError):
    """应用未安装错误。"""

    def __init__(self, app_package: str) -> None:
        super().__init__(
            f"App not installed: {app_package}",
            app_package,
            {"error_code": "APP_NOT_INSTALLED"},
        )


class AppLaunchError(AppError):
    """应用启动失败错误。"""

    def __init__(self, app_package: str, reason: str) -> None:
        super().__init__(
            f"Failed to launch app {app_package}: {reason}",
            app_package,
            {"error_code": "APP_LAUNCH_ERROR", "reason": reason},
        )


class ConfigurationError(AppiumMCPError):
    """配置相关错误。"""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "CONFIGURATION_ERROR", details)
        self.config_key = config_key


class InvalidConfigError(ConfigurationError):
    """无效配置错误。"""

    def __init__(self, config_key: str, value: Any, expected: str) -> None:
        super().__init__(
            f"Invalid configuration for '{config_key}': got {value}, expected {expected}",
            config_key,
            {
                "error_code": "INVALID_CONFIG",
                "key": config_key,
                "value": value,
                "expected": expected,
            },
        )


class ToolError(AppiumMCPError):
    """工具执行错误。"""

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "TOOL_ERROR", details)
        self.tool_name = tool_name


class ToolNotFoundError(ToolError):
    """工具未找到错误。"""

    def __init__(self, tool_name: str) -> None:
        super().__init__(
            f"Tool not found: {tool_name}",
            tool_name,
            {"error_code": "TOOL_NOT_FOUND"},
        )


class ToolTimeoutError(ToolError):
    """工具执行超时错误。"""

    def __init__(self, tool_name: str, timeout: int) -> None:
        super().__init__(
            f"Tool {tool_name} timed out after {timeout} seconds",
            tool_name,
            {"error_code": "TOOL_TIMEOUT", "timeout": timeout},
        )


class ValidationError(AppiumMCPError):
    """参数验证错误。"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field
        self.value = value


class FileOperationError(AppiumMCPError):
    """文件操作错误。"""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "FILE_OPERATION_ERROR", details)
        self.file_path = file_path
        self.operation = operation


class NetworkError(AppiumMCPError):
    """网络相关错误。"""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "NETWORK_ERROR", details)
        self.url = url
        self.status_code = status_code 