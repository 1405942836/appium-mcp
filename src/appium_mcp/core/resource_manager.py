"""
资源管理器。

负责管理MCP资源，包括设备信息、会话状态、截图等。
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
from mcp.types import Resource, TextResourceContents, BlobResourceContents

from .device_manager import DeviceManager
from .session_manager import SessionManager
from ..utils.exceptions import AppiumMCPError
from ..utils.helpers import format_duration, format_file_size

logger = structlog.get_logger(__name__)


class ResourceManager:
    """MCP资源管理器。"""

    def __init__(
        self,
        device_manager: DeviceManager,
        session_manager: SessionManager,
    ) -> None:
        """
        初始化资源管理器。

        Args:
            device_manager: 设备管理器
            session_manager: 会话管理器
        """
        self.device_manager = device_manager
        self.session_manager = session_manager
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}

    async def list_resources(self) -> List[Resource]:
        """
        列出所有可用资源。

        Returns:
            资源列表
        """
        resources = []

        # 设备列表资源
        resources.append(
            Resource(
                uri="appium://devices",
                name="设备列表",
                description="所有可用移动设备的列表",
                mimeType="application/json",
            )
        )

        # 会话列表资源
        resources.append(
            Resource(
                uri="appium://sessions",
                name="会话列表",
                description="所有活动会话的列表",
                mimeType="application/json",
            )
        )

        # 系统状态资源
        resources.append(
            Resource(
                uri="appium://status",
                name="系统状态",
                description="Appium MCP服务器状态信息",
                mimeType="application/json",
            )
        )

        # 配置信息资源
        resources.append(
            Resource(
                uri="appium://config",
                name="配置信息",
                description="当前服务器配置信息",
                mimeType="application/json",
            )
        )

        # 动态添加设备特定资源
        devices = self.device_manager.get_all_devices()
        for device in devices:
            resources.append(
                Resource(
                    uri=f"appium://device/{device.device_id}",
                    name=f"设备信息 - {device.name}",
                    description=f"{device.platform.title()} 设备 {device.name} 的详细信息",
                    mimeType="application/json",
                )
            )

        # 动态添加会话特定资源
        sessions = self.session_manager.get_all_sessions()
        for session in sessions:
            resources.append(
                Resource(
                    uri=f"appium://session/{session.session_id}",
                    name=f"会话信息 - {session.device_info.name}",
                    description=f"会话 {session.session_id} 的详细信息",
                    mimeType="application/json",
                )
            )

            # 会话截图资源
            resources.append(
                Resource(
                    uri=f"appium://session/{session.session_id}/screenshot",
                    name=f"截图 - {session.device_info.name}",
                    description=f"会话 {session.session_id} 的当前屏幕截图",
                    mimeType="image/png",
                )
            )

        # 添加日志文件资源
        log_files = self._get_log_files()
        for log_file in log_files:
            resources.append(
                Resource(
                    uri=f"file://{log_file}",
                    name=f"日志文件 - {log_file.name}",
                    description=f"日志文件: {log_file.name}",
                    mimeType="text/plain",
                )
            )

        return resources

    async def read_resource(self, uri: str) -> TextResourceContents | BlobResourceContents:
        """
        读取指定资源。

        Args:
            uri: 资源URI

        Returns:
            资源内容

        Raises:
            AppiumMCPError: 资源读取失败
        """
        logger.info("Reading resource", uri=uri)

        try:
            # 检查缓存
            cached_content = self._get_cached_content(uri)
            if cached_content is not None:
                return cached_content

            # 根据URI类型读取资源
            if uri == "appium://devices":
                content = await self._get_devices_resource()
            elif uri == "appium://sessions":
                content = await self._get_sessions_resource()
            elif uri == "appium://status":
                content = await self._get_status_resource()
            elif uri == "appium://config":
                content = await self._get_config_resource()
            elif uri.startswith("appium://device/"):
                device_id = uri.split("/")[-1]
                content = await self._get_device_resource(device_id)
            elif uri.startswith("appium://session/") and uri.endswith("/screenshot"):
                session_id = uri.split("/")[-2]
                return await self._get_screenshot_resource(session_id)
            elif uri.startswith("appium://session/"):
                session_id = uri.split("/")[-1]
                content = await self._get_session_resource(session_id)
            elif uri.startswith("file://"):
                file_path = uri[7:]  # 移除 "file://" 前缀
                return await self._get_file_resource(file_path)
            else:
                raise AppiumMCPError(f"Unknown resource URI: {uri}")

            # 缓存内容
            self._cache_content(uri, content)

            return TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=content,
            )

        except Exception as e:
            logger.error("Failed to read resource", uri=uri, error=str(e))
            raise AppiumMCPError(f"Failed to read resource {uri}: {e}")

    async def _get_devices_resource(self) -> str:
        """获取设备列表资源。"""
        devices = self.device_manager.get_all_devices()
        
        devices_data = {
            "devices": [device.to_dict() for device in devices],
            "total_count": len(devices),
            "platforms": {
                "android": len([d for d in devices if d.platform == "android"]),
                "ios": len([d for d in devices if d.platform == "ios"]),
            },
            "statuses": {
                "online": len([d for d in devices if d.status == "online"]),
                "offline": len([d for d in devices if d.status == "offline"]),
                "connected": len([d for d in devices if d.status == "connected"]),
            },
            "last_updated": time.time(),
        }
        
        import json
        return json.dumps(devices_data, indent=2, ensure_ascii=False)

    async def _get_sessions_resource(self) -> str:
        """获取会话列表资源。"""
        sessions = self.session_manager.get_all_sessions()
        stats = self.session_manager.get_session_stats()
        
        sessions_data = {
            "sessions": [session.to_dict() for session in sessions],
            "stats": stats,
            "last_updated": time.time(),
        }
        
        import json
        return json.dumps(sessions_data, indent=2, ensure_ascii=False)

    async def _get_status_resource(self) -> str:
        """获取系统状态资源。"""
        # 获取设备管理器状态
        devices = self.device_manager.get_all_devices()
        
        # 获取会话管理器状态
        session_stats = self.session_manager.get_session_stats()
        
        # 执行健康检查
        health_status = await self.session_manager.health_check()
        
        status_data = {
            "server": {
                "status": "running",
                "uptime": format_duration(time.time() - getattr(self, '_start_time', time.time())),
                "version": "1.0.0",
            },
            "devices": {
                "total": len(devices),
                "online": len([d for d in devices if d.status == "online"]),
                "connected": len([d for d in devices if d.status == "connected"]),
            },
            "sessions": session_stats,
            "health": health_status,
            "timestamp": time.time(),
        }
        
        import json
        return json.dumps(status_data, indent=2, ensure_ascii=False)

    async def _get_config_resource(self) -> str:
        """获取配置信息资源。"""
        # 这里应该从配置管理器获取配置信息
        # 为了演示，使用基本配置信息
        config_data = {
            "server": {
                "host": "localhost",
                "port": 4723,
                "timeout": 30,
            },
            "features": {
                "auto_screenshot": True,
                "performance_logging": True,
                "device_health_check": True,
            },
            "tools": {
                "enabled_categories": [
                    "device_management",
                    "ui_automation",
                    "app_control",
                    "system_operations",
                    "file_operations",
                ],
            },
            "last_updated": time.time(),
        }
        
        import json
        return json.dumps(config_data, indent=2, ensure_ascii=False)

    async def _get_device_resource(self, device_id: str) -> str:
        """获取单个设备资源。"""
        device_info = self.device_manager.get_device_info(device_id)
        
        if not device_info:
            raise AppiumMCPError(f"Device not found: {device_id}")
        
        # 检查是否有活动会话
        active_session = None
        for session in self.session_manager.get_all_sessions():
            if session.device_info.device_id == device_id:
                active_session = session.to_dict()
                break
        
        device_data = {
            "device_info": device_info.to_dict(),
            "active_session": active_session,
            "last_updated": time.time(),
        }
        
        import json
        return json.dumps(device_data, indent=2, ensure_ascii=False)

    async def _get_session_resource(self, session_id: str) -> str:
        """获取单个会话资源。"""
        try:
            session = await self.session_manager.get_session(session_id)
            
            session_data = {
                "session_info": session.to_dict(),
                "device_info": session.device_info.to_dict(),
                "last_updated": time.time(),
            }
            
            import json
            return json.dumps(session_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            raise AppiumMCPError(f"Session not found: {session_id}")

    async def _get_screenshot_resource(self, session_id: str) -> BlobResourceContents:
        """获取会话截图资源。"""
        try:
            session = await self.session_manager.get_session(session_id)
            
            # 获取截图
            screenshot_base64 = session.driver.get_screenshot_as_base64()
            
            import base64
            screenshot_data = base64.b64decode(screenshot_base64)
            
            return BlobResourceContents(
                uri=f"appium://session/{session_id}/screenshot",
                mimeType="image/png",
                blob=screenshot_data,
            )
            
        except Exception as e:
            raise AppiumMCPError(f"Failed to get screenshot for session {session_id}: {e}")

    async def _get_file_resource(self, file_path: str) -> TextResourceContents:
        """获取文件资源。"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise AppiumMCPError(f"File not found: {file_path}")
            
            # 读取文件内容
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return TextResourceContents(
                uri=f"file://{file_path}",
                mimeType="text/plain",
                text=content,
            )
            
        except Exception as e:
            raise AppiumMCPError(f"Failed to read file {file_path}: {e}")

    def _get_log_files(self) -> List[Path]:
        """获取日志文件列表。"""
        log_files = []
        
        # 查找常见的日志文件位置
        log_dirs = [
            Path("./logs"),
            Path("./"),
            Path.cwd() / "logs",
        ]
        
        for log_dir in log_dirs:
            if log_dir.exists() and log_dir.is_dir():
                for log_file in log_dir.glob("*.log"):
                    log_files.append(log_file)
        
        return log_files

    def _get_cached_content(self, uri: str) -> Optional[str]:
        """获取缓存内容。"""
        if uri in self._cache:
            # 检查缓存是否过期（TTL: 30秒）
            if time.time() - self._cache_ttl.get(uri, 0) < 30:
                return self._cache[uri]
            else:
                # 清理过期缓存
                del self._cache[uri]
                del self._cache_ttl[uri]
        
        return None

    def _cache_content(self, uri: str, content: str) -> None:
        """缓存内容。"""
        self._cache[uri] = content
        self._cache_ttl[uri] = time.time()
        
        # 限制缓存大小
        if len(self._cache) > 100:
            # 移除最旧的缓存项
            oldest_uri = min(self._cache_ttl.keys(), key=lambda k: self._cache_ttl[k])
            del self._cache[oldest_uri]
            del self._cache_ttl[oldest_uri]

    def clear_cache(self) -> None:
        """清理所有缓存。"""
        self._cache.clear()
        self._cache_ttl.clear()
        logger.info("Resource cache cleared") 