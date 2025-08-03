"""
会话管理器。

负责管理Appium会话的生命周期，包括会话创建、维护、超时处理和清理。
提供会话池和连接复用功能。
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Set

import structlog

from ..utils.exceptions import (
    SessionError,
    SessionNotFoundError,
    SessionTimeoutError,
)
from ..utils.helpers import generate_session_id, log_execution_time
from .device_manager import DeviceManager, DeviceSession

logger = structlog.get_logger(__name__)


class SessionPool:
    """会话池类。"""

    def __init__(self, max_sessions: int = 10, session_timeout: int = 300) -> None:
        """
        初始化会话池。

        Args:
            max_sessions: 最大会话数
            session_timeout: 会话超时时间（秒）
        """
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
        self._sessions: Dict[str, DeviceSession] = {}
        self._session_locks: Dict[str, asyncio.Lock] = {}

    async def get_session(self, session_id: str) -> Optional[DeviceSession]:
        """
        获取会话。

        Args:
            session_id: 会话ID

        Returns:
            会话对象，不存在返回None
        """
        session = self._sessions.get(session_id)
        if session:
            session.update_activity()
        return session

    async def add_session(self, session: DeviceSession) -> bool:
        """
        添加会话到池中。

        Args:
            session: 会话对象

        Returns:
            是否添加成功
        """
        if len(self._sessions) >= self.max_sessions:
            # 尝试清理过期会话
            await self.cleanup_expired_sessions()
            
            if len(self._sessions) >= self.max_sessions:
                logger.warning("Session pool is full", max_sessions=self.max_sessions)
                return False

        self._sessions[session.session_id] = session
        self._session_locks[session.session_id] = asyncio.Lock()
        
        logger.info(
            "Session added to pool",
            session_id=session.session_id,
            device_id=session.device_info.device_id,
            pool_size=len(self._sessions),
        )
        return True

    async def remove_session(self, session_id: str) -> Optional[DeviceSession]:
        """
        从池中移除会话。

        Args:
            session_id: 会话ID

        Returns:
            被移除的会话对象
        """
        session = self._sessions.pop(session_id, None)
        self._session_locks.pop(session_id, None)
        
        if session:
            logger.info(
                "Session removed from pool",
                session_id=session_id,
                device_id=session.device_info.device_id,
                pool_size=len(self._sessions),
            )
        
        return session

    async def get_session_lock(self, session_id: str) -> Optional[asyncio.Lock]:
        """获取会话锁。"""
        return self._session_locks.get(session_id)

    async def cleanup_expired_sessions(self) -> List[str]:
        """
        清理过期会话。

        Returns:
            被清理的会话ID列表
        """
        expired_sessions = []
        current_time = time.time()

        for session_id, session in list(self._sessions.items()):
            if current_time - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            await self.remove_session(session_id)

        if expired_sessions:
            logger.info(
                "Expired sessions cleaned up",
                expired_count=len(expired_sessions),
                remaining_sessions=len(self._sessions),
            )

        return expired_sessions

    def get_all_sessions(self) -> List[DeviceSession]:
        """获取所有会话。"""
        return list(self._sessions.values())

    def get_session_count(self) -> int:
        """获取会话数量。"""
        return len(self._sessions)

    def is_full(self) -> bool:
        """检查会话池是否已满。"""
        return len(self._sessions) >= self.max_sessions


class SessionManager:
    """会话管理器。"""

    def __init__(
        self,
        device_manager: DeviceManager,
        max_sessions: int = 10,
        session_timeout: int = 300,
        cleanup_interval: int = 60,
    ) -> None:
        """
        初始化会话管理器。

        Args:
            device_manager: 设备管理器
            max_sessions: 最大会话数
            session_timeout: 会话超时时间（秒）
            cleanup_interval: 清理间隔时间（秒）
        """
        self.device_manager = device_manager
        self.session_timeout = session_timeout
        self.cleanup_interval = cleanup_interval
        
        self._session_pool = SessionPool(max_sessions, session_timeout)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """启动会话管理器。"""
        if self._running:
            return

        logger.info("Starting session manager")
        self._running = True

        # MCP模式下禁用后台清理任务，避免干扰stdio通信
        logger.info("MCP mode: Disabling background cleanup tasks to prevent stdio interference")

    async def stop(self) -> None:
        """停止会话管理器。"""
        if not self._running:
            return

        logger.info("Stopping session manager")
        self._running = False

        # 取消清理任务
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # 关闭所有会话
        await self.close_all_sessions()

        # 等待任务完成
        if self._cleanup_task:
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        self._cleanup_task = None

    @log_execution_time
    async def create_session(
        self,
        device_id: str,
        capabilities: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> DeviceSession:
        """
        创建新会话。

        Args:
            device_id: 设备ID
            capabilities: 能力参数
            session_id: 自定义会话ID

        Returns:
            创建的会话

        Raises:
            SessionError: 会话创建失败
        """
        if not session_id:
            session_id = generate_session_id()

        logger.info(
            "Creating session",
            session_id=session_id,
            device_id=device_id,
            capabilities=capabilities,
        )

        try:
            # 检查会话池是否已满
            if self._session_pool.is_full():
                await self._session_pool.cleanup_expired_sessions()
                if self._session_pool.is_full():
                    raise SessionError(
                        "Session pool is full",
                        session_id,
                        {"max_sessions": self._session_pool.max_sessions},
                    )

            # 通过设备管理器连接设备
            session = await self.device_manager.connect_device(device_id, capabilities)
            
            # 将会话添加到池中
            success = await self._session_pool.add_session(session)
            if not success:
                # 如果添加失败，断开连接
                await self.device_manager.disconnect_device(session.session_id)
                raise SessionError(
                    "Failed to add session to pool",
                    session_id,
                )

            logger.info(
                "Session created successfully",
                session_id=session.session_id,
                device_id=device_id,
                platform=session.device_info.platform,
            )

            return session

        except Exception as e:
            logger.error(
                "Failed to create session",
                session_id=session_id,
                device_id=device_id,
                error=str(e),
            )
            raise SessionError(f"Failed to create session: {e}", session_id)

    async def get_session(self, session_id: str) -> DeviceSession:
        """
        获取会话。

        Args:
            session_id: 会话ID

        Returns:
            会话对象

        Raises:
            SessionNotFoundError: 会话不存在
            SessionTimeoutError: 会话超时
        """
        session = await self._session_pool.get_session(session_id)
        if not session:
            raise SessionNotFoundError(session_id)

        # 检查会话是否超时
        if session.is_expired(self.session_timeout):
            await self.close_session(session_id)
            raise SessionTimeoutError(session_id, self.session_timeout)

        return session

    async def close_session(self, session_id: str) -> None:
        """
        关闭会话。

        Args:
            session_id: 会话ID

        Raises:
            SessionError: 关闭失败
        """
        logger.info("Closing session", session_id=session_id)

        try:
            # 从池中移除会话
            session = await self._session_pool.remove_session(session_id)
            if not session:
                logger.warning("Session not found for closing", session_id=session_id)
                return

            # 通过设备管理器断开连接
            await self.device_manager.disconnect_device(session_id)

            logger.info(
                "Session closed successfully",
                session_id=session_id,
                device_id=session.device_info.device_id,
            )

        except Exception as e:
            logger.error("Failed to close session", session_id=session_id, error=str(e))
            raise SessionError(f"Failed to close session: {e}", session_id)

    async def close_all_sessions(self) -> None:
        """关闭所有会话。"""
        sessions = self._session_pool.get_all_sessions()
        logger.info("Closing all sessions", session_count=len(sessions))

        for session in sessions:
            try:
                await self.close_session(session.session_id)
            except Exception as e:
                logger.error(
                    "Failed to close session during shutdown",
                    session_id=session.session_id,
                    error=str(e),
                )

    async def refresh_session(self, session_id: str) -> DeviceSession:
        """
        刷新会话活动时间。

        Args:
            session_id: 会话ID

        Returns:
            刷新后的会话

        Raises:
            SessionNotFoundError: 会话不存在
        """
        session = await self.get_session(session_id)
        session.update_activity()
        
        logger.debug("Session refreshed", session_id=session_id)
        return session

    async def get_session_with_lock(self, session_id: str) -> tuple[DeviceSession, asyncio.Lock]:
        """
        获取会话和对应的锁。

        Args:
            session_id: 会话ID

        Returns:
            会话对象和锁

        Raises:
            SessionNotFoundError: 会话不存在
        """
        session = await self.get_session(session_id)
        lock = await self._session_pool.get_session_lock(session_id)
        
        if not lock:
            raise SessionError(f"Session lock not found: {session_id}", session_id)
        
        return session, lock

    def get_all_sessions(self) -> List[DeviceSession]:
        """获取所有会话信息。"""
        return self._session_pool.get_all_sessions()

    def get_session_count(self) -> int:
        """获取当前会话数量。"""
        return self._session_pool.get_session_count()

    def get_session_stats(self) -> Dict[str, Any]:
        """
        获取会话统计信息。

        Returns:
            统计信息字典
        """
        sessions = self.get_all_sessions()
        current_time = time.time()
        
        active_sessions = 0
        idle_sessions = 0
        platforms = {"android": 0, "ios": 0}
        
        for session in sessions:
            if current_time - session.last_activity < 60:  # 1分钟内活动
                active_sessions += 1
            else:
                idle_sessions += 1
            
            platform = session.device_info.platform
            if platform in platforms:
                platforms[platform] += 1

        return {
            "total_sessions": len(sessions),
            "active_sessions": active_sessions,
            "idle_sessions": idle_sessions,
            "max_sessions": self._session_pool.max_sessions,
            "session_timeout": self.session_timeout,
            "platforms": platforms,
            "pool_utilization": len(sessions) / self._session_pool.max_sessions,
        }

    async def cleanup_expired_sessions(self) -> List[str]:
        """
        手动清理过期会话。

        Returns:
            被清理的会话ID列表
        """
        logger.info("Manual session cleanup triggered")
        expired_sessions = await self._session_pool.cleanup_expired_sessions()
        
        # 通过设备管理器断开连接
        for session_id in expired_sessions:
            try:
                await self.device_manager.disconnect_device(session_id)
            except Exception as e:
                logger.error(
                    "Failed to disconnect expired session",
                    session_id=session_id,
                    error=str(e),
                )

        return expired_sessions

    async def _cleanup_loop(self) -> None:
        """清理循环任务。"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                if self._running:
                    await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Session cleanup loop error", error=str(e))

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查。

        Returns:
            健康状态信息
        """
        try:
            stats = self.get_session_stats()
            sessions = self.get_all_sessions()
            
            # 检查会话健康状态
            healthy_sessions = 0
            unhealthy_sessions = 0
            
            for session in sessions:
                try:
                    # 简单的健康检查：获取设备状态
                    session.driver.get_window_size()
                    healthy_sessions += 1
                except Exception:
                    unhealthy_sessions += 1

            return {
                "status": "healthy" if unhealthy_sessions == 0 else "degraded",
                "manager_running": self._running,
                "healthy_sessions": healthy_sessions,
                "unhealthy_sessions": unhealthy_sessions,
                "stats": stats,
            }

        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "manager_running": self._running,
            } 