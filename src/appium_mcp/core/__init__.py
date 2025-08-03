"""
核心模块包。

包含配置管理、设备管理、会话管理等核心功能。
"""

from .config_manager import ConfigManager, AppiumMCPConfig
from .device_manager import DeviceManager, DeviceInfo, DeviceSession
from .session_manager import SessionManager, SessionPool
from .resource_manager import ResourceManager
from .prompt_manager import PromptManager

__all__ = [
    "ConfigManager",
    "AppiumMCPConfig", 
    "DeviceManager",
    "DeviceInfo",
    "DeviceSession",
    "SessionManager",
    "SessionPool",
    "ResourceManager",
    "PromptManager",
] 