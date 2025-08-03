"""
配置管理器。

负责加载、验证和管理Appium MCP服务器的配置。
支持YAML配置文件、环境变量和命令行参数。
"""

import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from pydantic import BaseModel, Field, validator

from ..utils.exceptions import ConfigurationError, InvalidConfigError


class ServerConfig(BaseModel):
    """服务器配置。"""

    host: str = "localhost"
    port: int = 4723
    timeout: int = 30
    new_command_timeout: int = 60
    max_connections: int = 50
    connection_pool_size: int = 10
    allow_cors: bool = True
    allowed_origins: list[str] = ["*"]

    @validator("port")
    def validate_port(cls, v: int) -> int:
        """验证端口号。"""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @validator("timeout", "new_command_timeout")
    def validate_timeout(cls, v: int) -> int:
        """验证超时时间。"""
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v


class DeviceConfig(BaseModel):
    """设备配置。"""

    platform_name: str
    automation_name: str
    device_name: str
    implicit_wait: int = 10
    explicit_wait: int = 30
    no_reset: bool = False
    full_reset: bool = False


class AndroidConfig(DeviceConfig):
    """Android设备配置。"""

    platform_name: str = "Android"
    automation_name: str = "UiAutomator2"
    device_name: str = "Android Device"
    skip_server_installation: bool = False
    skip_device_initialization: bool = False
    chrome_driver_executable: Optional[str] = None
    chrome_options: list[str] = Field(
        default_factory=lambda: ["--no-sandbox", "--disable-dev-shm-usage"]
    )


class IOSConfig(DeviceConfig):
    """iOS设备配置。"""

    platform_name: str = "iOS"
    automation_name: str = "XCUITest"
    device_name: str = "iPhone Simulator"
    use_new_wda: bool = True
    wda_local_port: int = 8100
    wda_startup_retries: int = 2
    wda_startup_retry_interval: int = 20000
    xcode_org_id: Optional[str] = None
    xcode_signing_id: Optional[str] = None
    updated_wda_bundle_id: Optional[str] = None


class LoggingConfig(BaseModel):
    """日志配置。"""

    level: str = "INFO"
    console: bool = True
    file: Optional[str] = "appium-mcp.log"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_file_size: str = "10MB"
    backup_count: int = 5
    structured: bool = True
    json_format: bool = False

    @validator("level")
    def validate_level(cls, v: str) -> str:
        """验证日志级别。"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()


class FeaturesConfig(BaseModel):
    """功能特性配置。"""

    auto_screenshot: bool = True
    screenshot_on_error: bool = True
    screenshot_format: str = "png"
    element_highlight: bool = True
    highlight_color: str = "#FF0000"
    highlight_duration: int = 1000
    performance_logging: bool = True
    performance_metrics: list[str] = Field(
        default_factory=lambda: ["cpu", "memory", "network", "battery"]
    )
    screen_recording: bool = True
    recording_format: str = "mp4"
    recording_quality: str = "medium"
    auto_detect_devices: bool = True
    device_health_check: bool = True
    health_check_interval: int = 30

    @validator("screenshot_format")
    def validate_screenshot_format(cls, v: str) -> str:
        """验证截图格式。"""
        if v.lower() not in ["png", "jpg", "jpeg"]:
            raise ValueError("Screenshot format must be png or jpg")
        return v.lower()

    @validator("recording_quality")
    def validate_recording_quality(cls, v: str) -> str:
        """验证录制质量。"""
        if v.lower() not in ["low", "medium", "high"]:
            raise ValueError("Recording quality must be low, medium, or high")
        return v.lower()


class ToolsConfig(BaseModel):
    """工具配置。"""

    enabled: list[str] = Field(
        default_factory=lambda: [
            "device_management",
            "ui_automation",
            "app_control",
            "system_operations",
            "file_operations",
        ]
    )
    timeouts: Dict[str, int] = Field(
        default_factory=lambda: {
            "find_element": 10,
            "click_element": 5,
            "input_text": 10,
            "screenshot": 15,
            "file_transfer": 60,
        }
    )
    retries: Dict[str, Union[int, bool]] = Field(
        default_factory=lambda: {
            "max_attempts": 3,
            "retry_delay": 1,
            "exponential_backoff": True,
        }
    )


class ResourcesConfig(BaseModel):
    """资源配置。"""

    cache: Dict[str, Union[bool, int, str]] = Field(
        default_factory=lambda: {
            "enabled": True,
            "ttl": 300,
            "max_size": 100,
        }
    )
    storage: Dict[str, Union[str, bool, int]] = Field(
        default_factory=lambda: {
            "screenshots_dir": "./screenshots",
            "recordings_dir": "./recordings",
            "logs_dir": "./logs",
            "temp_dir": "./temp",
            "auto_cleanup": True,
            "cleanup_interval": 3600,
            "max_age": 86400,
        }
    )


class AppiumMCPConfig(BaseModel):
    """Appium MCP服务器完整配置。"""

    server: ServerConfig = Field(default_factory=ServerConfig)
    android: AndroidConfig = Field(default_factory=AndroidConfig)
    ios: IOSConfig = Field(default_factory=IOSConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    resources: ResourcesConfig = Field(default_factory=ResourcesConfig)


class ConfigManager:
    """配置管理器。"""

    def __init__(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        初始化配置管理器。

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self._config_path = self._resolve_config_path(config_path)
        self._config: Optional[AppiumMCPConfig] = None

    def _resolve_config_path(self, config_path: Optional[Union[str, Path]]) -> Path:
        """解析配置文件路径。"""
        if config_path:
            return Path(config_path)

        # 检查是否在 Cursor/MCP 环境中，强制使用本地配置
        if (os.environ.get("APPIUM_MCP_FORCE_LOCAL_CONFIG") == "1" or 
            os.environ.get("APPIUM_MCP_CONFIG_DIR")):
            # 优先使用环境变量指定的目录
            if config_dir_env := os.environ.get("APPIUM_MCP_CONFIG_DIR"):
                return Path(config_dir_env) / "config.yaml"
            # 否则使用当前工作目录
            return Path.cwd() / "config.yaml"

        # 使用默认配置文件路径
        system = platform.system().lower()
        if system == "windows":
            config_dir = Path(os.environ.get("APPDATA", "")) / "appium-mcp"
        else:
            config_dir = Path.home() / ".config" / "appium-mcp"

        return config_dir / "config.yaml"

    def load_config(self) -> AppiumMCPConfig:
        """
        加载配置。

        Returns:
            加载的配置对象

        Raises:
            ConfigurationError: 配置加载失败
        """
        try:
            # 先加载默认配置
            config_data = {}

            # 如果配置文件存在，加载文件配置
            if self._config_path.exists():
                with open(self._config_path, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        config_data.update(file_config)

            # 应用环境变量覆盖
            self._apply_env_overrides(config_data)

            # 创建配置对象
            self._config = AppiumMCPConfig(**config_data)
            return self._config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> None:
        """应用环境变量覆盖。"""
        env_mappings = {
            "APPIUM_MCP_SERVER_HOST": ["server", "host"],
            "APPIUM_MCP_SERVER_PORT": ["server", "port"],
            "APPIUM_MCP_SERVER_TIMEOUT": ["server", "timeout"],
            "APPIUM_MCP_LOG_LEVEL": ["logging", "level"],
            "APPIUM_MCP_LOG_FILE": ["logging", "file"],
            "APPIUM_MCP_AUTO_SCREENSHOT": ["features", "auto_screenshot"],
            "APPIUM_MCP_PERFORMANCE_LOGGING": ["features", "performance_logging"],
        }

        for env_key, config_path in env_mappings.items():
            env_value = os.environ.get(env_key)
            if env_value is not None:
                # 转换环境变量值的类型
                converted_value = self._convert_env_value(env_value)
                self._set_nested_config(config_data, config_path, converted_value)

    def _convert_env_value(self, value: str) -> Any:
        """转换环境变量值的类型。"""
        # 布尔值转换
        if value.lower() in ("true", "1", "yes", "on"):
            return True
        elif value.lower() in ("false", "0", "no", "off"):
            return False

        # 数字转换
        if value.isdigit():
            return int(value)

        try:
            return float(value)
        except ValueError:
            pass

        # 默认返回字符串
        return value

    def _set_nested_config(
        self, config_data: Dict[str, Any], path: list[str], value: Any
    ) -> None:
        """设置嵌套配置值。"""
        current = config_data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    def get_config(self) -> AppiumMCPConfig:
        """
        获取当前配置。

        Returns:
            当前配置对象

        Raises:
            ConfigurationError: 配置未加载
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded. Call load_config() first.")
        return self._config

    def save_config(self, config: Optional[AppiumMCPConfig] = None) -> None:
        """
        保存配置到文件。

        Args:
            config: 要保存的配置，如果为None则保存当前配置

        Raises:
            ConfigurationError: 配置保存失败
        """
        if config is None:
            config = self.get_config()

        try:
            # 确保配置目录存在
            self._config_path.parent.mkdir(parents=True, exist_ok=True)

            # 转换为字典并保存
            config_dict = config.dict()
            with open(self._config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    config_dict,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )

        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")

    def validate_config(self, config: Optional[AppiumMCPConfig] = None) -> bool:
        """
        验证配置。

        Args:
            config: 要验证的配置，如果为None则验证当前配置

        Returns:
            配置是否有效

        Raises:
            InvalidConfigError: 配置无效
        """
        if config is None:
            config = self.get_config()

        try:
            # Pydantic会在创建对象时自动验证
            # 这里可以添加额外的业务逻辑验证
            self._validate_business_logic(config)
            return True

        except Exception as e:
            raise InvalidConfigError("config", str(config), f"Valid configuration: {e}")

    def _validate_business_logic(self, config: AppiumMCPConfig) -> None:
        """验证业务逻辑。"""
        # 验证端口不冲突
        if config.server.port == config.ios.wda_local_port:
            raise ValueError("Server port and WDA local port cannot be the same")

        # 验证存储目录路径
        for key, path in config.resources.storage.items():
            if key.endswith("_dir") and isinstance(path, str):
                if not path or path.isspace():
                    raise ValueError(f"Storage directory '{key}' cannot be empty")

    @property
    def config_path(self) -> Path:
        """获取配置文件路径。"""
        return self._config_path

    def reload_config(self) -> AppiumMCPConfig:
        """重新加载配置。"""
        self._config = None
        return self.load_config()

    def create_default_config(self) -> None:
        """创建默认配置文件。"""
        default_config = AppiumMCPConfig()
        self.save_config(default_config) 