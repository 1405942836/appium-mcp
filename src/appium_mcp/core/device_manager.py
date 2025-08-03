"""
设备管理器。

负责移动设备的发现、连接、状态管理和基本操作。
支持Android和iOS设备及模拟器。
"""

import asyncio
import subprocess
import time
from typing import Any, Dict, List, Optional, Set

import structlog
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions

from ..utils.exceptions import (
    DeviceConnectionError,
    DeviceError,
    DeviceNotFoundError,
)
from ..utils.helpers import (
    get_platform_from_device_id,
    log_execution_time,
    retry_async,
    timeout_async,
    validate_device_id,
)

logger = structlog.get_logger(__name__)


class DeviceInfo:
    """设备信息类。"""

    def __init__(
        self,
        device_id: str,
        platform: str,
        name: str,
        version: str,
        status: str = "offline",
        **kwargs: Any,
    ) -> None:
        """
        初始化设备信息。

        Args:
            device_id: 设备ID
            platform: 平台类型 (android/ios)
            name: 设备名称
            version: 系统版本
            status: 设备状态
            **kwargs: 其他设备属性
        """
        self.device_id = device_id
        self.platform = platform.lower()
        self.name = name
        self.version = version
        self.status = status
        self.last_seen = time.time()
        self.properties = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "device_id": self.device_id,
            "platform": self.platform,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "last_seen": self.last_seen,
            "properties": self.properties,
        }

    def update_status(self, status: str) -> None:
        """更新设备状态。"""
        self.status = status
        self.last_seen = time.time()


class DeviceSession:
    """设备会话类。"""

    def __init__(
        self,
        device_info: DeviceInfo,
        driver: webdriver.Remote,
        session_id: str,
    ) -> None:
        """
        初始化设备会话。

        Args:
            device_info: 设备信息
            driver: Appium驱动实例
            session_id: 会话ID
        """
        self.device_info = device_info
        self.driver = driver
        self.session_id = session_id
        self.created_at = time.time()
        self.last_activity = time.time()

    def update_activity(self) -> None:
        """更新最后活动时间。"""
        self.last_activity = time.time()

    def is_expired(self, timeout: int = 300) -> bool:
        """检查会话是否过期。"""
        return time.time() - self.last_activity > timeout

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "session_id": self.session_id,
            "device_info": self.device_info.to_dict(),
            "created_at": self.created_at,
            "last_activity": self.last_activity,
        }


class DeviceManager:
    """设备管理器。"""

    def __init__(self, appium_server_url: str = "http://localhost:4723") -> None:
        """
        初始化设备管理器。

        Args:
            appium_server_url: Appium服务器URL
        """
        self.appium_server_url = appium_server_url
        self._devices: Dict[str, DeviceInfo] = {}
        self._sessions: Dict[str, DeviceSession] = {}
        self._discovery_tasks: Set[asyncio.Task] = set()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """启动设备管理器。"""
        if self._running:
            return

        logger.info("Starting device manager", server_url=self.appium_server_url)
        self._running = True

        # MCP模式：立即返回，不阻塞MCP握手
        # 设备发现改为后台异步执行，避免阻塞stdio通信
        logger.info("MCP mode: Starting device discovery in background to prevent blocking")
        
        # 启动后台设备发现任务，但不等待完成
        asyncio.create_task(self._background_device_discovery())

    async def stop(self) -> None:
        """停止设备管理器。"""
        if not self._running:
            return

        logger.info("Stopping device manager")
        self._running = False

        # 取消所有任务
        for task in self._discovery_tasks:
            task.cancel()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # 关闭所有会话
        await self._close_all_sessions()

        # 等待任务完成
        await asyncio.gather(*self._discovery_tasks, return_exceptions=True)
        if self._cleanup_task:
            await asyncio.gather(self._cleanup_task, return_exceptions=True)

        self._discovery_tasks.clear()
        self._cleanup_task = None

    @log_execution_time
    async def discover_devices(self) -> List[DeviceInfo]:
        """
        发现可用设备。

        Returns:
            发现的设备列表
        """
        logger.info("Discovering devices")
        discovered_devices = []

        try:
            # 并行发现Android和iOS设备
            logger.info("Starting Android and iOS device discovery tasks")
            tasks = [
                asyncio.create_task(self._discover_android_devices()),
                asyncio.create_task(self._discover_ios_devices()),
            ]

            logger.info("Waiting for device discovery tasks to complete")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Device discovery tasks completed, got {len(results)} results")

            for i, result in enumerate(results):
                if isinstance(result, list):
                    logger.info(f"Task {i} returned {len(result)} devices")
                    discovered_devices.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Task {i} failed with exception", error=str(result), exc_info=True)
                else:
                    logger.warning(f"Task {i} returned unexpected result type: {type(result)}")
        except Exception as e:
            logger.error("Critical error during device discovery", error=str(e), exc_info=True)
            raise

        # 更新设备列表
        for device in discovered_devices:
            self._devices[device.device_id] = device

        logger.info(
            "Device discovery completed",
            total_devices=len(discovered_devices),
            android_devices=len([d for d in discovered_devices if d.platform == "android"]),
            ios_devices=len([d for d in discovered_devices if d.platform == "ios"]),
        )

        return discovered_devices

    async def _background_device_discovery(self) -> None:
        """后台设备发现任务，带超时保护。"""
        try:
            logger.info("Starting background device discovery with timeout protection")
            
            # 设置5秒超时，避免阻塞太久
            try:
                await asyncio.wait_for(self.discover_devices(), timeout=5.0)
                logger.info("Background device discovery completed successfully")
            except asyncio.TimeoutError:
                logger.warning("Device discovery timed out after 5 seconds, continuing without devices")
                # 超时不是致命错误，服务器仍然可以工作
            
        except Exception as e:
            logger.error("Background device discovery failed", error=str(e), exc_info=True)
            # 设备发现失败不应该影响MCP服务器运行

    async def _discover_android_devices(self) -> List[DeviceInfo]:
        """发现Android设备。"""
        devices = []
        
        try:
            # 使用adb命令获取设备列表
            result = await asyncio.create_subprocess_exec(
                "adb", "devices", "-l",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                logger.warning("adb devices failed", stderr=stderr.decode())
                return devices

            # 解析adb输出
            lines = stdout.decode().strip().split("\n")[1:]  # 跳过标题行
            
            for line in lines:
                if not line.strip() or "offline" in line:
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                device_id = parts[0]
                status = "online" if parts[1] == "device" else "offline"

                # 获取设备详细信息，带超时保护
                try:
                    device_info = await asyncio.wait_for(
                        self._get_android_device_info(device_id), 
                        timeout=3.0  # 3秒超时
                    )
                    if device_info:
                        device_info.update_status(status)
                        devices.append(device_info)
                except asyncio.TimeoutError:
                    logger.warning(f"Getting device info for {device_id} timed out, skipping")
                    # 创建基本设备信息，不获取详细属性
                    basic_device = DeviceInfo(
                        device_id=device_id,
                        platform="android",
                        name=f"Android Device {device_id}",
                        version="Unknown",
                        status=status
                    )
                    devices.append(basic_device)

        except Exception as e:
            logger.error("Failed to discover Android devices", error=str(e), exc_info=True)

        return devices

    async def _get_android_device_info(self, device_id: str) -> Optional[DeviceInfo]:
        """获取Android设备详细信息。"""
        try:
            # 获取设备属性
            props_result = await asyncio.create_subprocess_exec(
                "adb", "-s", device_id, "shell", "getprop",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await props_result.communicate()

            if props_result.returncode != 0:
                return None

            # 解析属性
            properties = {}
            for line in stdout.decode().split("\n"):
                if ": [" in line and line.endswith("]"):
                    key, value = line.split(": [", 1)
                    key = key.strip("[]")
                    value = value.rstrip("]")
                    properties[key] = value

            # 提取关键信息
            name = properties.get("ro.product.model", "Unknown Android Device")
            version = properties.get("ro.build.version.release", "Unknown")
            manufacturer = properties.get("ro.product.manufacturer", "")
            brand = properties.get("ro.product.brand", "")

            return DeviceInfo(
                device_id=device_id,
                platform="android",
                name=f"{brand} {name}".strip() or name,
                version=version,
                manufacturer=manufacturer,
                brand=brand,
                sdk_version=properties.get("ro.build.version.sdk", ""),
                abi=properties.get("ro.product.cpu.abi", ""),
            )

        except Exception as e:
            logger.warning("Failed to get Android device info", device_id=device_id, error=str(e))
            return None

    async def _discover_ios_devices(self) -> List[DeviceInfo]:
        """发现iOS设备。"""
        devices = []
        
        try:
            import platform
            # 在非macOS系统上跳过iOS设备发现
            if platform.system() != "Darwin":
                logger.info("Skipping iOS device discovery on non-macOS system")
                return devices
                
            # 使用xcrun simctl获取模拟器列表
            result = await asyncio.create_subprocess_exec(
                "xcrun", "simctl", "list", "devices", "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                logger.warning("xcrun simctl failed", stderr=stderr.decode())
                return devices

            # 解析JSON输出
            import json
            data = json.loads(stdout.decode())
            
            for runtime, device_list in data.get("devices", {}).items():
                if "iOS" not in runtime:
                    continue

                ios_version = runtime.split("iOS-")[-1].replace("-", ".")
                
                for device in device_list:
                    if device.get("availability") == "(available)":
                        device_info = DeviceInfo(
                            device_id=device["udid"],
                            platform="ios",
                            name=device["name"],
                            version=ios_version,
                            status="available" if device["state"] == "Booted" else "shutdown",
                            device_type=device.get("deviceTypeIdentifier", ""),
                            runtime=runtime,
                        )
                        devices.append(device_info)

            # 尝试获取真机设备 (需要安装ios-deploy或类似工具)
            try:
                real_devices = await self._discover_ios_real_devices()
                devices.extend(real_devices)
            except Exception as e:
                logger.debug("Failed to discover iOS real devices", error=str(e))

        except Exception as e:
            logger.error("Failed to discover iOS devices", error=str(e))

        return devices

    async def _discover_ios_real_devices(self) -> List[DeviceInfo]:
        """发现iOS真机设备。"""
        devices = []
        
        try:
            # 使用idevice_id获取真机设备列表
            result = await asyncio.create_subprocess_exec(
                "idevice_id", "-l",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                return devices

            device_ids = stdout.decode().strip().split("\n")
            
            for device_id in device_ids:
                if device_id.strip():
                    device_info = await self._get_ios_device_info(device_id.strip())
                    if device_info:
                        devices.append(device_info)

        except FileNotFoundError:
            # idevice_id 未安装
            pass
        except Exception as e:
            logger.warning("Failed to discover iOS real devices", error=str(e))

        return devices

    async def _get_ios_device_info(self, device_id: str) -> Optional[DeviceInfo]:
        """获取iOS设备详细信息。"""
        try:
            # 使用ideviceinfo获取设备信息
            result = await asyncio.create_subprocess_exec(
                "ideviceinfo", "-u", device_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                return None

            # 解析设备信息
            properties = {}
            for line in stdout.decode().split("\n"):
                if ": " in line:
                    key, value = line.split(": ", 1)
                    properties[key.strip()] = value.strip()

            name = properties.get("DeviceName", "Unknown iOS Device")
            version = properties.get("ProductVersion", "Unknown")

            return DeviceInfo(
                device_id=device_id,
                platform="ios",
                name=name,
                version=version,
                status="online",
                product_type=properties.get("ProductType", ""),
                build_version=properties.get("BuildVersion", ""),
            )

        except Exception as e:
            logger.warning("Failed to get iOS device info", device_id=device_id, error=str(e))
            return None

    @timeout_async(30)
    @retry_async(max_attempts=3)
    async def connect_device(
        self,
        device_id: str,
        capabilities: Optional[Dict[str, Any]] = None,
    ) -> DeviceSession:
        """
        连接到设备并创建会话。

        Args:
            device_id: 设备ID
            capabilities: 自定义能力参数

        Returns:
            设备会话

        Raises:
            DeviceNotFoundError: 设备不存在
            DeviceConnectionError: 连接失败
        """
        if not validate_device_id(device_id):
            raise DeviceNotFoundError(device_id)

        device_info = self._devices.get(device_id)
        if not device_info:
            # 尝试重新发现设备
            await self.discover_devices()
            device_info = self._devices.get(device_id)
            if not device_info:
                raise DeviceNotFoundError(device_id)

        # 检查是否已有活动会话
        existing_session = self._get_active_session(device_id)
        if existing_session:
            existing_session.update_activity()
            return existing_session

        logger.info("Connecting to device", device_id=device_id, platform=device_info.platform)

        try:
            # 创建驱动选项
            if device_info.platform == "android":
                options = UiAutomator2Options()
                options.device_name = device_info.name
                options.udid = device_id
                options.platform_name = "Android"
                options.automation_name = "UiAutomator2"
            elif device_info.platform == "ios":
                options = XCUITestOptions()
                options.device_name = device_info.name
                options.udid = device_id
                options.platform_name = "iOS"
                options.automation_name = "XCUITest"
            else:
                raise DeviceConnectionError(device_id, f"Unsupported platform: {device_info.platform}")

            # 应用自定义能力
            if capabilities:
                for key, value in capabilities.items():
                    setattr(options, key, value)

            # 创建驱动实例
            driver = webdriver.Remote(self.appium_server_url, options=options)
            
            # 生成会话ID
            session_id = driver.session_id
            
            # 创建会话对象
            session = DeviceSession(device_info, driver, session_id)
            self._sessions[session_id] = session

            # 更新设备状态
            device_info.update_status("connected")

            logger.info(
                "Device connected successfully",
                device_id=device_id,
                session_id=session_id,
                platform=device_info.platform,
            )

            return session

        except Exception as e:
            logger.error("Failed to connect device", device_id=device_id, error=str(e))
            raise DeviceConnectionError(device_id, str(e))

    async def disconnect_device(self, session_id: str) -> None:
        """
        断开设备连接。

        Args:
            session_id: 会话ID

        Raises:
            DeviceError: 断开连接失败
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.warning("Session not found for disconnect", session_id=session_id)
            return

        try:
            logger.info("Disconnecting device", session_id=session_id, device_id=session.device_info.device_id)
            
            # 关闭驱动
            session.driver.quit()
            
            # 移除会话
            del self._sessions[session_id]
            
            # 更新设备状态
            session.device_info.update_status("online")

            logger.info("Device disconnected successfully", session_id=session_id)

        except Exception as e:
            logger.error("Failed to disconnect device", session_id=session_id, error=str(e))
            raise DeviceError(f"Failed to disconnect device: {e}")

    def get_device_info(self, device_id: str) -> Optional[DeviceInfo]:
        """获取设备信息。"""
        return self._devices.get(device_id)

    def get_all_devices(self) -> List[DeviceInfo]:
        """获取所有设备信息。"""
        return list(self._devices.values())

    def get_session(self, session_id: str) -> Optional[DeviceSession]:
        """获取会话信息。"""
        return self._sessions.get(session_id)

    def get_all_sessions(self) -> List[DeviceSession]:
        """获取所有会话信息。"""
        return list(self._sessions.values())

    def _get_active_session(self, device_id: str) -> Optional[DeviceSession]:
        """获取设备的活动会话。"""
        for session in self._sessions.values():
            if session.device_info.device_id == device_id:
                return session
        return None

    async def _discover_devices_loop(self) -> None:
        """设备发现循环任务。"""
        while self._running:
            try:
                await asyncio.sleep(30)  # 每30秒发现一次
                if self._running:
                    await self.discover_devices()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Device discovery loop error", error=str(e))

    async def _cleanup_loop(self) -> None:
        """清理循环任务。"""
        while self._running:
            try:
                await asyncio.sleep(60)  # 每分钟清理一次
                if self._running:
                    await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Cleanup loop error", error=str(e))

    async def _cleanup_expired_sessions(self) -> None:
        """清理过期会话。"""
        expired_sessions = []
        
        for session_id, session in self._sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            try:
                await self.disconnect_device(session_id)
                logger.info("Cleaned up expired session", session_id=session_id)
            except Exception as e:
                logger.error("Failed to cleanup expired session", session_id=session_id, error=str(e))

    async def _close_all_sessions(self) -> None:
        """关闭所有会话。"""
        session_ids = list(self._sessions.keys())
        
        for session_id in session_ids:
            try:
                await self.disconnect_device(session_id)
            except Exception as e:
                logger.error("Failed to close session", session_id=session_id, error=str(e)) 