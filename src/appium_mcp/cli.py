"""
Appium MCP服务器命令行接口。

提供启动、配置、状态查看等命令行功能。
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
import structlog

from .server import AppiumMCPServer, get_server_instance
from .core.config_manager import ConfigManager
from .utils.exceptions import AppiumMCPError

logger = structlog.get_logger(__name__)


@click.group()
@click.version_option(version="1.0.0", prog_name="appium-mcp-server")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="配置文件路径",
)
@click.option(
    "--log-level",
    "-l",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="日志级别",
)
@click.pass_context
def cli(ctx: click.Context, config: Optional[Path], log_level: str) -> None:
    """
    Appium MCP Server - 移动设备自动化测试的MCP服务器。

    提供基于Model Context Protocol的移动设备自动化测试服务，
    支持Android和iOS设备的连接、控制和自动化测试。
    """
    # 配置日志
    _configure_logging(log_level)
    
    # 保存配置到上下文
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = str(config) if config else None
    ctx.obj["log_level"] = log_level


@cli.command()
@click.pass_context
def run(ctx: click.Context) -> None:
    """启动MCP服务器（stdio模式）。"""
    config_path = ctx.obj.get("config_path")
    
    # 移除emoji输出，避免JSON解析错误
    # click.echo("🚀 启动 Appium MCP Server...")
    # click.echo(f"📁 配置文件: {config_path or '默认配置'}")
    
    try:
        # 创建并运行服务器
        server = get_server_instance(config_path)
        asyncio.run(server.run_stdio())
        
    except KeyboardInterrupt:
        # 移除emoji输出，避免JSON解析错误
        pass
    except Exception as e:
        # 输出错误到stderr，避免干扰MCP通信
        sys.stderr.write(f"Server startup failed: {e}\n")
        sys.exit(1)


@cli.command()
@click.pass_context
def init_config(ctx: click.Context) -> None:
    """生成默认配置文件。"""
    config_path = ctx.obj.get("config_path")
    
    try:
        config_manager = ConfigManager(config_path)
        config_manager.create_default_config()
        
        actual_path = config_manager.config_path
        click.echo(f"✅ 默认配置文件已生成: {actual_path}")
        click.echo(f"📝 请编辑配置文件以满足您的需求")
        
    except Exception as e:
        click.echo(f"❌ 配置文件生成失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def show_config(ctx: click.Context) -> None:
    """显示当前配置。"""
    config_path = ctx.obj.get("config_path")
    
    try:
        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()
        
        click.echo(f"📁 配置文件路径: {config_manager.config_path}")
        click.echo("📋 当前配置:")
        click.echo(json.dumps(config.dict(), indent=2, ensure_ascii=False))
        
    except Exception as e:
        click.echo(f"❌ 配置加载失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def validate_config(ctx: click.Context) -> None:
    """验证配置文件。"""
    config_path = ctx.obj.get("config_path")
    
    try:
        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()
        
        # 验证配置
        is_valid = config_manager.validate_config(config)
        
        if is_valid:
            click.echo("✅ 配置文件验证通过")
        else:
            click.echo("❌ 配置文件验证失败")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ 配置验证失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
async def status(ctx: click.Context) -> None:
    """显示服务器状态（需要服务器运行中）。"""
    config_path = ctx.obj.get("config_path")
    
    try:
        # 注意：这个命令需要服务器正在运行才能获取状态
        # 在实际实现中，可能需要通过其他方式（如HTTP API）获取状态
        click.echo("ℹ️  此命令需要服务器正在运行")
        click.echo("💡 请在另一个终端中运行 'appium-mcp-server run' 启动服务器")
        
    except Exception as e:
        click.echo(f"❌ 获取状态失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["android", "ios"]),
    help="过滤特定平台的设备",
)
def list_devices(platform: Optional[str]) -> None:
    """列出可用设备（需要Appium服务器运行）。"""
    click.echo("📱 正在扫描可用设备...")
    
    try:
        # 创建临时的设备管理器来扫描设备
        from .core.device_manager import DeviceManager
        
        async def scan_devices():
            device_manager = DeviceManager()
            await device_manager.start()
            
            try:
                devices = await device_manager.discover_devices()
                
                if platform:
                    devices = [d for d in devices if d.platform == platform.lower()]
                
                if not devices:
                    click.echo("❌ 未找到可用设备")
                    return
                
                click.echo(f"✅ 找到 {len(devices)} 个设备:")
                click.echo()
                
                for device in devices:
                    status_emoji = "🟢" if device.status == "online" else "🔴"
                    platform_emoji = "🤖" if device.platform == "android" else "🍎"
                    
                    click.echo(f"{status_emoji} {platform_emoji} {device.name}")
                    click.echo(f"   ID: {device.device_id}")
                    click.echo(f"   平台: {device.platform.title()}")
                    click.echo(f"   版本: {device.version}")
                    click.echo(f"   状态: {device.status}")
                    click.echo()
                    
            finally:
                await device_manager.stop()
        
        asyncio.run(scan_devices())
        
    except Exception as e:
        click.echo(f"❌ 设备扫描失败: {e}", err=True)
        click.echo("💡 请确保:")
        click.echo("   - Appium服务器正在运行")
        click.echo("   - Android: ADB已安装且设备已连接")
        click.echo("   - iOS: Xcode已安装且模拟器可用")
        sys.exit(1)


@cli.command()
def version() -> None:
    """显示版本信息。"""
    click.echo("Appium MCP Server v1.0.0")
    click.echo("基于Model Context Protocol的移动设备自动化测试服务器")
    click.echo()
    click.echo("依赖组件:")
    
    # 检查依赖版本
    try:
        import appium
        click.echo(f"  • Appium Python Client: {appium.__version__}")
    except ImportError:
        click.echo("  • Appium Python Client: 未安装")
    
    try:
        import mcp
        click.echo(f"  • MCP SDK: {mcp.__version__}")
    except (ImportError, AttributeError):
        click.echo("  • MCP SDK: 版本未知")
    
    try:
        import pydantic
        click.echo(f"  • Pydantic: {pydantic.VERSION}")
    except ImportError:
        click.echo("  • Pydantic: 未安装")


@cli.command()
def doctor() -> None:
    """检查系统环境和依赖。"""
    click.echo("🩺 Appium MCP Server 环境检查")
    click.echo()
    
    issues = []
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version >= (3, 9):
        click.echo(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        click.echo(f"❌ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro} (需要 >= 3.9)")
        issues.append("Python版本过低")
    
    # 检查必需依赖
    required_packages = [
        ("mcp", "MCP SDK"),
        ("appium", "Appium Python Client"),
        ("pydantic", "Pydantic"),
        ("structlog", "Structured Logging"),
        ("click", "Click CLI"),
    ]
    
    for package, name in required_packages:
        try:
            __import__(package)
            click.echo(f"✅ {name}: 已安装")
        except ImportError:
            click.echo(f"❌ {name}: 未安装")
            issues.append(f"{name}未安装")
    
    # 检查系统工具
    import subprocess
    import shutil
    
    system_tools = [
        ("adb", "Android Debug Bridge", "Android设备连接"),
        ("xcrun", "Xcode Command Line Tools", "iOS设备连接 (仅macOS)"),
    ]
    
    for tool, name, description in system_tools:
        if shutil.which(tool):
            click.echo(f"✅ {name}: 已安装")
        else:
            click.echo(f"⚠️  {name}: 未找到 ({description})")
    
    # 检查Appium服务器
    try:
        import requests
        response = requests.get("http://localhost:4723/status", timeout=5)
        if response.status_code == 200:
            click.echo("✅ Appium服务器: 运行中")
        else:
            click.echo("⚠️  Appium服务器: 响应异常")
    except Exception:
        click.echo("⚠️  Appium服务器: 未运行或无法连接")
    
    # 总结
    click.echo()
    if issues:
        click.echo(f"❌ 发现 {len(issues)} 个问题:")
        for issue in issues:
            click.echo(f"   • {issue}")
        click.echo()
        click.echo("💡 请解决上述问题后重新运行检查")
        sys.exit(1)
    else:
        click.echo("🎉 环境检查通过！所有依赖都已正确安装")


def _configure_logging(level: str) -> None:
    """配置日志系统。"""
    import logging
    
    # 配置标准库日志级别
    logging.basicConfig(level=getattr(logging, level))
    
    # 配置structlog
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
            structlog.dev.ConsoleRenderer() if level == "DEBUG" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def main() -> None:
    """主函数入口。"""
    try:
        cli()
    except Exception as e:
        click.echo(f"❌ 命令执行失败: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 