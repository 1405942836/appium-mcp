"""
Appium MCP服务器主类。

整合所有组件，实现完整的MCP服务器功能。
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Sequence

import structlog
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .core.config_manager import ConfigManager, AppiumMCPConfig
from .core.device_manager import DeviceManager
from .core.session_manager import SessionManager
from .core.resource_manager import ResourceManager
from .core.prompt_manager import PromptManager
from .tools.device_tools import (
    ListDevicesTool,
    ConnectDeviceTool,
    DisconnectDeviceTool,
    GetDeviceInfoTool,
    GetSessionInfoTool,
    ListSessionsTool,
    CleanupSessionsTool,
    RefreshDevicesTool,
)
from .tools.ui_tools import (
    FindElementTool,
    ClickElementTool,
    InputTextTool,
    TakeScreenshotTool,
    SwipeTool,
)
from .utils.exceptions import AppiumMCPError

logger = structlog.get_logger(__name__)


class AppiumMCPServer:
    """Appium MCP服务器主类。"""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        初始化Appium MCP服务器。

        Args:
            config_path: 配置文件路径
        """
        # 初始化配置管理器
        self.config_manager = ConfigManager(config_path)
        self.config: Optional[AppiumMCPConfig] = None

        # 初始化核心组件
        self.device_manager: Optional[DeviceManager] = None
        self.session_manager: Optional[SessionManager] = None
        self.resource_manager: Optional[ResourceManager] = None
        self.prompt_manager: Optional[PromptManager] = None

        # 初始化MCP服务器
        self.mcp_server = Server("appium-mcp-server")
        self.tools: List[Any] = []

        # 服务器状态
        self._running = False
        self._start_time = 0.0

    async def initialize(self) -> None:
        """初始化服务器组件。"""
        logger.info("Initializing Appium MCP Server")

        try:
            # 加载配置
            self.config = self.config_manager.load_config()
            logger.info("Configuration loaded successfully")

            # 初始化设备管理器
            appium_url = f"http://{self.config.server.host}:{self.config.server.port}"
            self.device_manager = DeviceManager(appium_url)

            # 初始化会话管理器
            self.session_manager = SessionManager(
                device_manager=self.device_manager,
                max_sessions=self.config.server.max_connections,
                session_timeout=self.config.server.new_command_timeout,
            )

            # 初始化资源管理器
            self.resource_manager = ResourceManager(
                device_manager=self.device_manager,
                session_manager=self.session_manager,
            )

            # 初始化提示管理器
            self.prompt_manager = PromptManager()

            # 初始化工具
            self._initialize_tools()

            # 注册MCP处理器
            self._register_handlers()

            logger.info("Appium MCP Server initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize server", error=str(e))
            raise AppiumMCPError(f"Server initialization failed: {e}")

    def _initialize_tools(self) -> None:
        """初始化工具列表。"""
        logger.info("Initializing tools")

        # 设备管理工具
        self.tools.extend([
            ListDevicesTool(self.session_manager),
            ConnectDeviceTool(self.session_manager),
            DisconnectDeviceTool(self.session_manager),
            GetDeviceInfoTool(self.session_manager),
            GetSessionInfoTool(self.session_manager),
            ListSessionsTool(self.session_manager),
            CleanupSessionsTool(self.session_manager),
            RefreshDevicesTool(self.session_manager),
        ])

        # UI自动化工具
        self.tools.extend([
            FindElementTool(self.session_manager),
            ClickElementTool(self.session_manager),
            InputTextTool(self.session_manager),
            TakeScreenshotTool(self.session_manager),
            SwipeTool(self.session_manager),
        ])

        logger.info("Tools initialized", tool_count=len(self.tools))

    def _register_handlers(self) -> None:
        """注册MCP处理器。"""
        logger.info("Registering MCP handlers")

        # 注册工具列表处理器
        @self.mcp_server.list_tools()
        async def list_tools() -> List[types.Tool]:
            """列出所有可用工具。"""
            return [tool.to_mcp_tool() for tool in self.tools]

        # 注册工具调用处理器
        @self.mcp_server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """调用指定工具。"""
            logger.info("Tool called", name=name, arguments=arguments)

            # 查找工具
            tool = None
            for t in self.tools:
                if t.name == name:
                    tool = t
                    break

            if not tool:
                raise AppiumMCPError(f"Tool not found: {name}")

            try:
                # 执行工具
                result = await tool.safe_execute(arguments)
                
                # 格式化返回结果
                result_text = json.dumps(result, indent=2, ensure_ascii=False)
                
                return [
                    types.TextContent(
                        type="text",
                        text=result_text,
                    )
                ]

            except Exception as e:
                logger.error("Tool execution failed", name=name, error=str(e))
                error_result = {
                    "success": False,
                    "error": str(e),
                    "tool_name": name,
                }
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(error_result, indent=2, ensure_ascii=False),
                    )
                ]

        # 注册资源列表处理器
        @self.mcp_server.list_resources()
        async def list_resources() -> List[types.Resource]:
            """列出所有可用资源。"""
            if not self.resource_manager:
                return []
            return await self.resource_manager.list_resources()

        # 注册资源读取处理器
        @self.mcp_server.read_resource()
        async def read_resource(uri: str) -> types.TextResourceContents | types.BlobResourceContents:
            """读取指定资源。"""
            if not self.resource_manager:
                raise AppiumMCPError("Resource manager not initialized")
            return await self.resource_manager.read_resource(uri)

        # 注册提示列表处理器
        @self.mcp_server.list_prompts()
        async def list_prompts() -> List[types.Prompt]:
            """列出所有可用提示模板。"""
            if not self.prompt_manager:
                return []
            return self.prompt_manager.list_prompts()

        # 注册提示获取处理器
        @self.mcp_server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, Any]) -> types.GetPromptResult:
            """获取指定提示模板。"""
            if not self.prompt_manager:
                raise AppiumMCPError("Prompt manager not initialized")
            
            messages = self.prompt_manager.get_prompt(name, arguments)
            return types.GetPromptResult(messages=messages)

        logger.info("MCP handlers registered successfully")

    async def start(self) -> None:
        """启动服务器。"""
        if self._running:
            logger.warning("Server is already running")
            return

        logger.info("Starting Appium MCP Server")

        try:
            import time
            self._start_time = time.time()
            self._running = True

            # 启动核心组件
            if self.device_manager:
                await self.device_manager.start()

            if self.session_manager:
                await self.session_manager.start()

            logger.info("Appium MCP Server started successfully")

        except Exception as e:
            logger.error("Failed to start server", error=str(e))
            self._running = False
            raise AppiumMCPError(f"Server start failed: {e}")

    async def stop(self) -> None:
        """停止服务器。"""
        if not self._running:
            return

        logger.info("Stopping Appium MCP Server")

        try:
            self._running = False

            # 停止核心组件
            if self.session_manager:
                await self.session_manager.stop()

            if self.device_manager:
                await self.device_manager.stop()

            logger.info("Appium MCP Server stopped successfully")

        except Exception as e:
            logger.error("Failed to stop server", error=str(e))
            raise AppiumMCPError(f"Server stop failed: {e}")

    async def run_stdio(self) -> None:
        """以stdio模式运行服务器。"""
        logger.info("Starting MCP server in stdio mode")

        try:
            # 初始化服务器
            await self.initialize()
            await self.start()

            # 运行stdio服务器
            async with stdio_server() as (read_stream, write_stream):
                await self.mcp_server.run(
                    read_stream,
                    write_stream,
                    self.mcp_server.create_initialization_options(),
                )

        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error("Server error", error=str(e))
            raise
        finally:
            await self.stop()

    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息。"""
        import time
        
        uptime = time.time() - self._start_time if self._running else 0
        
        info = {
            "name": "Appium MCP Server",
            "version": "1.0.0",
            "status": "running" if self._running else "stopped",
            "uptime": uptime,
            "config": {
                "server": self.config.server.dict() if self.config else {},
                "features": self.config.features.dict() if self.config else {},
            },
            "stats": {
                "tools_count": len(self.tools),
                "devices_count": len(self.device_manager.get_all_devices()) if self.device_manager else 0,
                "sessions_count": self.session_manager.get_session_count() if self.session_manager else 0,
            },
        }

        return info

    async def health_check(self) -> Dict[str, Any]:
        """执行健康检查。"""
        try:
            health_info = {
                "status": "healthy",
                "timestamp": time.time(),
                "components": {},
            }

            # 检查设备管理器
            if self.device_manager:
                try:
                    devices = self.device_manager.get_all_devices()
                    health_info["components"]["device_manager"] = {
                        "status": "healthy",
                        "devices_count": len(devices),
                    }
                except Exception as e:
                    health_info["components"]["device_manager"] = {
                        "status": "unhealthy",
                        "error": str(e),
                    }
                    health_info["status"] = "degraded"

            # 检查会话管理器
            if self.session_manager:
                try:
                    session_health = await self.session_manager.health_check()
                    health_info["components"]["session_manager"] = session_health
                    
                    if session_health["status"] != "healthy":
                        health_info["status"] = "degraded"
                        
                except Exception as e:
                    health_info["components"]["session_manager"] = {
                        "status": "unhealthy",
                        "error": str(e),
                    }
                    health_info["status"] = "degraded"

            return health_info

        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time(),
            }


# 全局服务器实例
_server_instance: Optional[AppiumMCPServer] = None


def get_server_instance(config_path: Optional[str] = None) -> AppiumMCPServer:
    """
    获取服务器实例（单例模式）。

    Args:
        config_path: 配置文件路径

    Returns:
        服务器实例
    """
    global _server_instance
    
    if _server_instance is None:
        _server_instance = AppiumMCPServer(config_path)
    
    return _server_instance


async def main() -> None:
    """主函数。"""
    # 配置日志
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 创建并运行服务器
    server = get_server_instance()
    await server.run_stdio()


if __name__ == "__main__":
    asyncio.run(main()) 