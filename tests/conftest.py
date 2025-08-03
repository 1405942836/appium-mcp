"""
Pytest配置和共用fixture。
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
from typing import AsyncGenerator, Generator

from appium_mcp.core.config_manager import ConfigManager, AppiumMCPConfig
from appium_mcp.core.device_manager import DeviceManager, DeviceInfo
from appium_mcp.core.session_manager import SessionManager
from appium_mcp.server import AppiumMCPServer


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环用于异步测试。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config() -> AppiumMCPConfig:
    """创建模拟配置。"""
    return AppiumMCPConfig()


@pytest.fixture
def config_manager(tmp_path: Path) -> ConfigManager:
    """创建配置管理器。"""
    config_path = tmp_path / "test_config.yaml"
    return ConfigManager(config_path)


@pytest.fixture
def mock_device_info() -> DeviceInfo:
    """创建模拟设备信息。"""
    return DeviceInfo(
        device_id="test_device_001",
        platform="android",
        name="Test Device",
        version="11.0",
        status="online",
        manufacturer="Test Manufacturer",
        brand="Test Brand",
    )


@pytest.fixture
def mock_ios_device_info() -> DeviceInfo:
    """创建模拟iOS设备信息。"""
    return DeviceInfo(
        device_id="test_ios_device_001",
        platform="ios",
        name="iPhone 13 Simulator",
        version="15.0",
        status="available",
        device_type="com.apple.CoreSimulator.SimDeviceType.iPhone-13",
        runtime="iOS 15.0",
    )


@pytest.fixture
async def device_manager() -> AsyncGenerator[DeviceManager, None]:
    """创建设备管理器。"""
    manager = DeviceManager("http://localhost:4723")
    yield manager
    await manager.stop()


@pytest.fixture
async def session_manager(device_manager: DeviceManager) -> AsyncGenerator[SessionManager, None]:
    """创建会话管理器。"""
    manager = SessionManager(device_manager)
    yield manager
    await manager.stop()


@pytest.fixture
async def mock_appium_driver():
    """创建模拟Appium驱动。"""
    mock_driver = MagicMock()
    mock_driver.session_id = "test_session_123"
    mock_driver.get_screenshot_as_base64 = MagicMock(return_value="fake_base64_data")
    mock_driver.get_window_size = MagicMock(return_value={"width": 1080, "height": 1920})
    mock_driver.quit = MagicMock()
    
    # 模拟元素查找
    mock_element = MagicMock()
    mock_element.id = "element_123"
    mock_element.tag_name = "android.widget.TextView"
    mock_element.text = "Test Element"
    mock_element.is_enabled.return_value = True
    mock_element.is_displayed.return_value = True
    mock_element.is_selected.return_value = False
    mock_element.location = {"x": 100, "y": 200}
    mock_element.size = {"width": 200, "height": 50}
    mock_element.rect = {"x": 100, "y": 200, "width": 200, "height": 50}
    mock_element.get_attribute = MagicMock(return_value="test_value")
    mock_element.click = MagicMock()
    mock_element.send_keys = MagicMock()
    mock_element.clear = MagicMock()
    
    mock_driver.find_element.return_value = mock_element
    mock_driver.swipe = MagicMock()
    
    return mock_driver


@pytest.fixture
def mock_webdriver_wait():
    """创建模拟WebDriverWait。"""
    mock_wait = MagicMock()
    mock_element = MagicMock()
    mock_element.id = "element_123"
    mock_element.tag_name = "android.widget.TextView"
    mock_element.text = "Test Element"
    mock_element.is_enabled.return_value = True
    mock_element.is_displayed.return_value = True
    mock_element.is_selected.return_value = False
    mock_element.location = {"x": 100, "y": 200}
    mock_element.size = {"width": 200, "height": 50}
    mock_element.rect = {"x": 100, "y": 200, "width": 200, "height": 50}
    mock_element.get_attribute = MagicMock(return_value="test_value")
    mock_element.click = MagicMock()
    mock_element.send_keys = MagicMock()
    mock_element.clear = MagicMock()
    
    mock_wait.until.return_value = mock_element
    return mock_wait


@pytest.fixture
async def appium_server(tmp_path: Path) -> AsyncGenerator[AppiumMCPServer, None]:
    """创建Appium MCP服务器实例。"""
    config_path = tmp_path / "test_config.yaml"
    server = AppiumMCPServer(str(config_path))
    
    # 创建默认配置文件
    server.config_manager.create_default_config()
    
    yield server
    
    if server._running:
        await server.stop()


# 标记配置
pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    """Pytest配置。"""
    # 添加自定义标记
    config.addinivalue_line("markers", "unit: 单元测试标记")
    config.addinivalue_line("markers", "integration: 集成测试标记")
    config.addinivalue_line("markers", "slow: 慢速测试标记")
    config.addinivalue_line("markers", "android: Android相关测试")
    config.addinivalue_line("markers", "ios: iOS相关测试") 