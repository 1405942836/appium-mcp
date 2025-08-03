"""
工具模块单元测试。
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from appium_mcp.tools.device_tools import (
    ListDevicesTool,
    ConnectDeviceTool,
    DisconnectDeviceTool,
    GetDeviceInfoTool,
)
from appium_mcp.tools.ui_tools import (
    FindElementTool,
    ClickElementTool,
    InputTextTool,
    TakeScreenshotTool,
    SwipeTool,
)
from appium_mcp.utils.exceptions import ValidationError, ToolError


@pytest.mark.unit
class TestDeviceTools:
    """设备工具测试类。"""

    @pytest.mark.asyncio
    async def test_list_devices_tool(self, session_manager):
        """测试列出设备工具。"""
        # 模拟设备列表
        mock_device1 = MagicMock()
        mock_device1.to_dict.return_value = {
            "device_id": "device1",
            "platform": "android",
            "status": "online"
        }
        
        mock_device2 = MagicMock()
        mock_device2.to_dict.return_value = {
            "device_id": "device2", 
            "platform": "ios",
            "status": "offline"
        }
        
        session_manager.device_manager.get_all_devices.return_value = [
            mock_device1, mock_device2
        ]
        
        tool = ListDevicesTool(session_manager)
        
        # 测试列出所有设备
        result = await tool.execute({})
        
        assert result["total_count"] == 2
        assert len(result["devices"]) == 2
        assert result["platforms"]["android"] == 1
        assert result["platforms"]["ios"] == 1

    @pytest.mark.asyncio
    async def test_list_devices_tool_with_filter(self, session_manager):
        """测试带过滤器的列出设备工具。"""
        mock_device = MagicMock()
        mock_device.platform = "android"
        mock_device.status = "online"
        mock_device.to_dict.return_value = {
            "device_id": "device1",
            "platform": "android",
            "status": "online"
        }
        
        session_manager.device_manager.get_all_devices.return_value = [mock_device]
        
        tool = ListDevicesTool(session_manager)
        
        # 测试平台过滤
        result = await tool.execute({"platform": "android"})
        assert result["total_count"] == 1
        
        # 测试过滤掉不匹配的平台
        result = await tool.execute({"platform": "ios"})
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_connect_device_tool(self, session_manager):
        """测试连接设备工具。"""
        # 模拟会话
        mock_session = MagicMock()
        mock_session.session_id = "session123"
        mock_session.device_info.to_dict.return_value = {
            "device_id": "device1",
            "platform": "android"
        }
        
        session_manager.create_session = AsyncMock(return_value=mock_session)
        
        tool = ConnectDeviceTool(session_manager)
        
        # 测试连接设备
        result = await tool.execute({
            "device_id": "device1",
            "app_package": "com.example.app"
        })
        
        assert result["session_id"] == "session123"
        assert result["status"] == "connected"
        assert "device_info" in result
        
        # 验证调用参数
        session_manager.create_session.assert_called_once_with(
            "device1", {"appPackage": "com.example.app"}
        )

    @pytest.mark.asyncio
    async def test_disconnect_device_tool(self, session_manager):
        """测试断开设备工具。"""
        # 模拟会话
        mock_session = MagicMock()
        mock_session.device_info.device_id = "device1"
        
        session_manager.get_session = AsyncMock(return_value=mock_session)
        session_manager.close_session = AsyncMock()
        
        tool = DisconnectDeviceTool(session_manager)
        
        # 测试断开连接
        result = await tool.execute({"session_id": "session123"})
        
        assert result["session_id"] == "session123"
        assert result["device_id"] == "device1"
        assert result["status"] == "disconnected"
        
        # 验证调用
        session_manager.get_session.assert_called_once_with("session123")
        session_manager.close_session.assert_called_once_with("session123")

    @pytest.mark.asyncio
    async def test_get_device_info_tool(self, session_manager):
        """测试获取设备信息工具。"""
        # 模拟设备信息
        mock_device = MagicMock()
        mock_device.to_dict.return_value = {
            "device_id": "device1",
            "platform": "android",
            "name": "Test Device"
        }
        
        session_manager.device_manager.get_device_info.return_value = mock_device
        
        tool = GetDeviceInfoTool(session_manager)
        
        # 测试获取设备信息
        result = await tool.execute({"device_id": "device1"})
        
        assert result["device_id"] == "device1"
        assert result["found"] is True
        assert "device_info" in result

    @pytest.mark.asyncio
    async def test_get_device_info_tool_not_found(self, session_manager):
        """测试获取不存在设备信息。"""
        session_manager.device_manager.get_device_info.return_value = None
        session_manager.device_manager.discover_devices = AsyncMock(return_value=[])
        
        tool = GetDeviceInfoTool(session_manager)
        
        # 测试设备不存在
        result = await tool.execute({"device_id": "nonexistent"})
        
        assert result["device_id"] == "nonexistent"
        assert result["found"] is False
        assert "error" in result


@pytest.mark.unit
class TestUITools:
    """UI工具测试类。"""

    @pytest.mark.asyncio
    async def test_find_element_tool(self, session_manager, mock_appium_driver, mock_webdriver_wait):
        """测试查找元素工具。"""
        # 模拟会话和锁
        mock_session = MagicMock()
        mock_session.driver = mock_appium_driver
        mock_lock = AsyncMock()
        
        session_manager.get_session_with_lock = AsyncMock(
            return_value=(mock_session, mock_lock)
        )
        
        tool = FindElementTool(session_manager)
        
        with patch('appium_mcp.tools.ui_tools.WebDriverWait', return_value=mock_webdriver_wait):
            result = await tool.execute({
                "session_id": "session123",
                "locator_type": "id",
                "locator_value": "test_id"
            })
        
        assert result["found"] is True
        assert "element" in result
        assert result["element"]["element_id"] == "element_123"
        assert result["locator"]["type"] == "id"
        assert result["locator"]["value"] == "test_id"

    @pytest.mark.asyncio
    async def test_click_element_tool(self, session_manager, mock_appium_driver, mock_webdriver_wait):
        """测试点击元素工具。"""
        # 模拟会话和锁
        mock_session = MagicMock()
        mock_session.driver = mock_appium_driver
        mock_lock = AsyncMock()
        
        session_manager.get_session_with_lock = AsyncMock(
            return_value=(mock_session, mock_lock)
        )
        
        tool = ClickElementTool(session_manager)
        
        with patch('appium_mcp.tools.ui_tools.WebDriverWait', return_value=mock_webdriver_wait):
            result = await tool.execute({
                "session_id": "session123",
                "locator_type": "id",
                "locator_value": "test_button"
            })
        
        assert result["success"] is True
        assert result["action"] == "click"
        
        # 验证点击被调用
        mock_element = mock_webdriver_wait.until.return_value
        mock_element.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_input_text_tool(self, session_manager, mock_appium_driver, mock_webdriver_wait):
        """测试输入文本工具。"""
        # 模拟会话和锁
        mock_session = MagicMock()
        mock_session.driver = mock_appium_driver
        mock_lock = AsyncMock()
        
        session_manager.get_session_with_lock = AsyncMock(
            return_value=(mock_session, mock_lock)
        )
        
        tool = InputTextTool(session_manager)
        
        with patch('appium_mcp.tools.ui_tools.WebDriverWait', return_value=mock_webdriver_wait):
            result = await tool.execute({
                "session_id": "session123",
                "locator_type": "id",
                "locator_value": "text_input",
                "text": "Hello World",
                "clear_first": True
            })
        
        assert result["success"] is True
        assert result["action"] == "input_text"
        assert result["text"] == "Hello World"
        
        # 验证清空和输入被调用
        mock_element = mock_webdriver_wait.until.return_value
        mock_element.clear.assert_called_once()
        mock_element.send_keys.assert_called_once_with("Hello World")

    @pytest.mark.asyncio
    async def test_take_screenshot_tool(self, session_manager, mock_appium_driver):
        """测试截图工具。"""
        # 模拟会话和锁
        mock_session = MagicMock()
        mock_session.driver = mock_appium_driver
        mock_session.device_info.name = "Test Device"
        mock_lock = AsyncMock()
        
        session_manager.get_session_with_lock = AsyncMock(
            return_value=(mock_session, mock_lock)
        )
        
        tool = TakeScreenshotTool(session_manager)
        
        with patch('pathlib.Path.mkdir'), patch('builtins.open', create=True):
            result = await tool.execute({
                "session_id": "session123",
                "format": "png"
            })
        
        assert result["success"] is True
        assert result["action"] == "screenshot"
        assert result["base64_data"] == "fake_base64_data"
        assert result["format"] == "png"
        
        # 验证截图被调用
        mock_appium_driver.get_screenshot_as_base64.assert_called_once()

    @pytest.mark.asyncio
    async def test_swipe_tool(self, session_manager, mock_appium_driver):
        """测试滑动工具。"""
        # 模拟会话和锁
        mock_session = MagicMock()
        mock_session.driver = mock_appium_driver
        mock_lock = AsyncMock()
        
        session_manager.get_session_with_lock = AsyncMock(
            return_value=(mock_session, mock_lock)
        )
        
        tool = SwipeTool(session_manager)
        
        result = await tool.execute({
            "session_id": "session123",
            "start_x": 100,
            "start_y": 200,
            "end_x": 300,
            "end_y": 400,
            "duration": 1500
        })
        
        assert result["success"] is True
        assert result["action"] == "swipe"
        assert result["start_point"] == {"x": 100, "y": 200}
        assert result["end_point"] == {"x": 300, "y": 400}
        assert result["duration"] == 1500
        
        # 验证滑动被调用
        mock_appium_driver.swipe.assert_called_once_with(100, 200, 300, 400, 1500)


@pytest.mark.unit
class TestToolValidation:
    """工具参数验证测试类。"""

    def test_tool_parameter_validation(self, session_manager):
        """测试工具参数验证。"""
        tool = ListDevicesTool(session_manager)
        
        # 有效参数
        tool.validate_arguments({"platform": "android"})
        
        # 无效枚举值
        with pytest.raises(ValidationError, match="must be one of"):
            tool.validate_arguments({"platform": "invalid"})

    def test_required_parameter_validation(self, session_manager):
        """测试必需参数验证。"""
        tool = ConnectDeviceTool(session_manager)
        
        # 缺少必需参数
        with pytest.raises(ValidationError, match="Missing required parameter"):
            tool.validate_arguments({})
        
        # 有效参数
        tool.validate_arguments({"device_id": "device1"})

    def test_parameter_type_validation(self, session_manager):
        """测试参数类型验证。"""
        tool = SwipeTool(session_manager)
        
        # 无效类型
        with pytest.raises(ValidationError, match="must be an integer"):
            tool.validate_arguments({
                "session_id": "session123",
                "start_x": "invalid",
                "start_y": 200,
                "end_x": 300,
                "end_y": 400
            })

    @pytest.mark.asyncio
    async def test_tool_error_handling(self, session_manager):
        """测试工具错误处理。"""
        # 模拟会话管理器抛出异常
        session_manager.device_manager.get_all_devices.side_effect = Exception("Test error")
        
        tool = ListDevicesTool(session_manager)
        
        with pytest.raises(ToolError, match="Test error"):
            await tool.safe_execute({})

    def test_tool_to_mcp_conversion(self, session_manager):
        """测试工具转换为MCP格式。"""
        tool = ListDevicesTool(session_manager)
        mcp_tool = tool.to_mcp_tool()
        
        assert mcp_tool.name == "list_devices"
        assert mcp_tool.description == "列出所有可用的移动设备（Android和iOS）"
        assert "inputSchema" in mcp_tool.dict()
        assert mcp_tool.inputSchema["type"] == "object"
        assert "properties" in mcp_tool.inputSchema 