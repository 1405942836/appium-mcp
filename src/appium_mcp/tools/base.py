"""
工具基类。

定义Appium MCP工具的基础接口和通用功能。
所有具体工具都应继承此基类。
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import structlog
from mcp.types import Tool

from ..core.session_manager import SessionManager
from ..utils.exceptions import ToolError, ValidationError
from ..utils.helpers import log_execution_time, timeout_async

logger = structlog.get_logger(__name__)


class AppiumTool(ABC):
    """Appium工具基类。"""

    def __init__(self, session_manager: SessionManager) -> None:
        """
        初始化工具。

        Args:
            session_manager: 会话管理器
        """
        self.session_manager = session_manager
        self.logger = structlog.get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称。"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述。"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """工具参数定义（JSON Schema格式）。"""
        pass

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具。

        Args:
            arguments: 工具参数

        Returns:
            执行结果

        Raises:
            ToolError: 工具执行失败
        """
        pass

    def to_mcp_tool(self) -> Tool:
        """转换为MCP工具定义。"""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": self.parameters,
                "required": self._get_required_parameters(),
            },
        )

    def _get_required_parameters(self) -> List[str]:
        """获取必需参数列表。"""
        required = []
        for param_name, param_def in self.parameters.items():
            if isinstance(param_def, dict) and not param_def.get("optional", False):
                required.append(param_name)
        return required

    def validate_arguments(self, arguments: Dict[str, Any]) -> None:
        """
        验证参数。

        Args:
            arguments: 工具参数

        Raises:
            ValidationError: 参数验证失败
        """
        required_params = self._get_required_parameters()
        
        # 检查必需参数
        for param in required_params:
            if param not in arguments:
                raise ValidationError(
                    f"Missing required parameter: {param}",
                    param,
                    None,
                )

        # 检查参数类型和值
        for param_name, param_value in arguments.items():
            if param_name in self.parameters:
                self._validate_parameter(param_name, param_value)

    def _validate_parameter(self, param_name: str, param_value: Any) -> None:
        """
        验证单个参数。

        Args:
            param_name: 参数名
            param_value: 参数值

        Raises:
            ValidationError: 参数验证失败
        """
        param_def = self.parameters.get(param_name, {})
        param_type = param_def.get("type")

        if param_type == "string" and not isinstance(param_value, str):
            raise ValidationError(
                f"Parameter '{param_name}' must be a string",
                param_name,
                param_value,
            )
        elif param_type == "integer" and not isinstance(param_value, int):
            raise ValidationError(
                f"Parameter '{param_name}' must be an integer",
                param_name,
                param_value,
            )
        elif param_type == "number" and not isinstance(param_value, (int, float)):
            raise ValidationError(
                f"Parameter '{param_name}' must be a number",
                param_name,
                param_value,
            )
        elif param_type == "boolean" and not isinstance(param_value, bool):
            raise ValidationError(
                f"Parameter '{param_name}' must be a boolean",
                param_name,
                param_value,
            )
        elif param_type == "array" and not isinstance(param_value, list):
            raise ValidationError(
                f"Parameter '{param_name}' must be an array",
                param_name,
                param_value,
            )
        elif param_type == "object" and not isinstance(param_value, dict):
            raise ValidationError(
                f"Parameter '{param_name}' must be an object",
                param_name,
                param_value,
            )

        # 检查枚举值
        enum_values = param_def.get("enum")
        if enum_values and param_value not in enum_values:
            raise ValidationError(
                f"Parameter '{param_name}' must be one of {enum_values}",
                param_name,
                param_value,
            )

        # 检查字符串长度
        if param_type == "string" and isinstance(param_value, str):
            min_length = param_def.get("minLength")
            max_length = param_def.get("maxLength")
            
            if min_length and len(param_value) < min_length:
                raise ValidationError(
                    f"Parameter '{param_name}' must be at least {min_length} characters",
                    param_name,
                    param_value,
                )
            
            if max_length and len(param_value) > max_length:
                raise ValidationError(
                    f"Parameter '{param_name}' must be at most {max_length} characters",
                    param_name,
                    param_value,
                )

        # 检查数值范围
        if param_type in ["integer", "number"] and isinstance(param_value, (int, float)):
            minimum = param_def.get("minimum")
            maximum = param_def.get("maximum")
            
            if minimum is not None and param_value < minimum:
                raise ValidationError(
                    f"Parameter '{param_name}' must be at least {minimum}",
                    param_name,
                    param_value,
                )
            
            if maximum is not None and param_value > maximum:
                raise ValidationError(
                    f"Parameter '{param_name}' must be at most {maximum}",
                    param_name,
                    param_value,
                )

    @log_execution_time
    async def safe_execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        安全执行工具，包含错误处理和日志记录。

        Args:
            arguments: 工具参数

        Returns:
            执行结果
        """
        try:
            self.logger.info(
                "Executing tool",
                tool_name=self.name,
                arguments=arguments,
            )

            # 验证参数
            self.validate_arguments(arguments)

            # 执行工具
            result = await self.execute(arguments)

            self.logger.info(
                "Tool executed successfully",
                tool_name=self.name,
                result_keys=list(result.keys()) if isinstance(result, dict) else None,
            )

            return result

        except Exception as e:
            self.logger.error(
                "Tool execution failed",
                tool_name=self.name,
                error=str(e),
                arguments=arguments,
            )
            raise ToolError(str(e), self.name)

    async def get_session_with_lock(self, session_id: str):
        """
        获取会话和锁。

        Args:
            session_id: 会话ID

        Returns:
            会话对象和锁
        """
        return await self.session_manager.get_session_with_lock(session_id)


class DeviceManagementTool(AppiumTool):
    """设备管理工具基类。"""
    
    @property
    def category(self) -> str:
        return "device_management"


class UIAutomationTool(AppiumTool):
    """UI自动化工具基类。"""
    
    @property
    def category(self) -> str:
        return "ui_automation"

    def _get_common_locator_parameters(self) -> Dict[str, Any]:
        """获取通用定位器参数定义。"""
        return {
            "locator_type": {
                "type": "string",
                "description": "元素定位器类型",
                "enum": [
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
                ],
            },
            "locator_value": {
                "type": "string",
                "description": "元素定位器值",
                "minLength": 1,
            },
        }


class AppControlTool(AppiumTool):
    """应用控制工具基类。"""
    
    @property
    def category(self) -> str:
        return "app_control"


class SystemOperationTool(AppiumTool):
    """系统操作工具基类。"""
    
    @property
    def category(self) -> str:
        return "system_operations"


class FileOperationTool(AppiumTool):
    """文件操作工具基类。"""
    
    @property
    def category(self) -> str:
        return "file_operations" 