"""
设备管理工具。

提供设备发现、连接、状态查询等功能。
"""

from typing import Any, Dict, List

from .base import DeviceManagementTool


class ListDevicesTool(DeviceManagementTool):
    """列出所有可用设备。"""

    @property
    def name(self) -> str:
        return "list_devices"

    @property
    def description(self) -> str:
        return "列出所有可用的移动设备（Android和iOS）"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "platform": {
                "type": "string",
                "description": "过滤特定平台的设备",
                "enum": ["android", "ios"],
                "optional": True,
            },
            "status": {
                "type": "string",
                "description": "过滤特定状态的设备",
                "enum": ["online", "offline", "connected"],
                "optional": True,
            },
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行设备列表查询。"""
        platform_filter = arguments.get("platform")
        status_filter = arguments.get("status")

        # 获取所有设备
        devices = self.session_manager.device_manager.get_all_devices()
        
        # 应用过滤器
        filtered_devices = []
        for device in devices:
            if platform_filter and device.platform != platform_filter.lower():
                continue
            if status_filter and device.status != status_filter.lower():
                continue
            filtered_devices.append(device.to_dict())

        return {
            "devices": filtered_devices,
            "total_count": len(filtered_devices),
            "platforms": {
                "android": len([d for d in filtered_devices if d["platform"] == "android"]),
                "ios": len([d for d in filtered_devices if d["platform"] == "ios"]),
            },
        }


class ConnectDeviceTool(DeviceManagementTool):
    """连接到指定设备。"""

    @property
    def name(self) -> str:
        return "connect_device"

    @property
    def description(self) -> str:
        return "连接到指定的移动设备并创建会话"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "device_id": {
                "type": "string",
                "description": "设备ID（从list_devices获取）",
                "minLength": 1,
            },
            "app_package": {
                "type": "string",
                "description": "要启动的Android应用包名",
                "optional": True,
            },
            "app_activity": {
                "type": "string",
                "description": "要启动的Android应用Activity",
                "optional": True,
            },
            "bundle_id": {
                "type": "string",
                "description": "要启动的iOS应用Bundle ID",
                "optional": True,
            },
            "no_reset": {
                "type": "boolean",
                "description": "是否在会话开始时重置应用状态",
                "optional": True,
            },
            "full_reset": {
                "type": "boolean",
                "description": "是否完全重置应用（卸载重装）",
                "optional": True,
            },
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行设备连接。"""
        device_id = arguments["device_id"]
        
        # 构建能力参数
        capabilities = {}
        
        if arguments.get("app_package"):
            capabilities["appPackage"] = arguments["app_package"]
        if arguments.get("app_activity"):
            capabilities["appActivity"] = arguments["app_activity"]
        if arguments.get("bundle_id"):
            capabilities["bundleId"] = arguments["bundle_id"]
        if arguments.get("no_reset") is not None:
            capabilities["noReset"] = arguments["no_reset"]
        if arguments.get("full_reset") is not None:
            capabilities["fullReset"] = arguments["full_reset"]

        # 创建会话
        session = await self.session_manager.create_session(device_id, capabilities)

        return {
            "session_id": session.session_id,
            "device_info": session.device_info.to_dict(),
            "capabilities": capabilities,
            "status": "connected",
        }


class DisconnectDeviceTool(DeviceManagementTool):
    """断开设备连接。"""

    @property
    def name(self) -> str:
        return "disconnect_device"

    @property
    def description(self) -> str:
        return "断开指定设备的连接并关闭会话"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "session_id": {
                "type": "string",
                "description": "会话ID（从connect_device获取）",
                "minLength": 1,
            },
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行设备断开连接。"""
        session_id = arguments["session_id"]
        
        # 获取会话信息
        session = await self.session_manager.get_session(session_id)
        device_id = session.device_info.device_id

        # 关闭会话
        await self.session_manager.close_session(session_id)

        return {
            "session_id": session_id,
            "device_id": device_id,
            "status": "disconnected",
        }


class GetDeviceInfoTool(DeviceManagementTool):
    """获取设备详细信息。"""

    @property
    def name(self) -> str:
        return "get_device_info"

    @property
    def description(self) -> str:
        return "获取指定设备的详细信息"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "device_id": {
                "type": "string",
                "description": "设备ID",
                "minLength": 1,
            },
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行设备信息查询。"""
        device_id = arguments["device_id"]
        
        device_info = self.session_manager.device_manager.get_device_info(device_id)
        if not device_info:
            # 尝试重新发现设备
            await self.session_manager.device_manager.discover_devices()
            device_info = self.session_manager.device_manager.get_device_info(device_id)
            
        if not device_info:
            return {
                "device_id": device_id,
                "found": False,
                "error": "Device not found",
            }

        return {
            "device_id": device_id,
            "found": True,
            "device_info": device_info.to_dict(),
        }


class GetSessionInfoTool(DeviceManagementTool):
    """获取会话信息。"""

    @property
    def name(self) -> str:
        return "get_session_info"

    @property
    def description(self) -> str:
        return "获取指定会话的详细信息"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "session_id": {
                "type": "string",
                "description": "会话ID",
                "minLength": 1,
            },
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行会话信息查询。"""
        session_id = arguments["session_id"]
        
        try:
            session = await self.session_manager.get_session(session_id)
            return {
                "session_id": session_id,
                "found": True,
                "session_info": session.to_dict(),
            }
        except Exception as e:
            return {
                "session_id": session_id,
                "found": False,
                "error": str(e),
            }


class ListSessionsTool(DeviceManagementTool):
    """列出所有活动会话。"""

    @property
    def name(self) -> str:
        return "list_sessions"

    @property
    def description(self) -> str:
        return "列出所有活动的设备会话"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {}

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行会话列表查询。"""
        sessions = self.session_manager.get_all_sessions()
        stats = self.session_manager.get_session_stats()

        return {
            "sessions": [session.to_dict() for session in sessions],
            "stats": stats,
        }


class CleanupSessionsTool(DeviceManagementTool):
    """手动清理过期会话。"""

    @property
    def name(self) -> str:
        return "cleanup_sessions"

    @property
    def description(self) -> str:
        return "手动清理过期的设备会话"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {}

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行会话清理。"""
        try:
            # 清理过期会话
            expired_sessions = await self.session_manager.cleanup_expired_sessions()
            
            # 重新发现设备
            await self.session_manager.device_manager.discover_devices()
            
            return {
                "success": True,
                "message": f"成功清理了 {len(expired_sessions)} 个过期会话",
                "expired_sessions": expired_sessions,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "清理会话时发生错误",
            }


class RefreshDevicesTool(DeviceManagementTool):
    """手动刷新设备列表。"""

    @property
    def name(self) -> str:
        return "refresh_devices"

    @property
    def description(self) -> str:
        return "手动刷新和重新发现移动设备"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {}

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行设备刷新。"""
        try:
            # 重新发现设备
            devices = await self.session_manager.device_manager.discover_devices()
            
            return {
                "success": True,
                "message": f"成功发现 {len(devices)} 个设备",
                "devices": [
                    {
                        "device_id": device.device_id,
                        "platform": device.platform,
                        "name": device.name,
                        "status": device.status,
                    }
                    for device in devices
                ],
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "刷新设备时发生错误",
            } 