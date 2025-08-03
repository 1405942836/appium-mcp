"""
配置管理器单元测试。
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from appium_mcp.core.config_manager import ConfigManager, AppiumMCPConfig
from appium_mcp.utils.exceptions import ConfigurationError, InvalidConfigError


@pytest.mark.unit
class TestConfigManager:
    """配置管理器测试类。"""

    def test_init_with_custom_path(self, tmp_path: Path):
        """测试使用自定义路径初始化。"""
        config_path = tmp_path / "custom_config.yaml"
        manager = ConfigManager(config_path)
        
        assert manager.config_path == config_path

    def test_init_with_default_path(self):
        """测试使用默认路径初始化。"""
        manager = ConfigManager()
        
        # 应该生成默认路径
        assert manager.config_path.name == "config.yaml"
        assert "appium-mcp" in str(manager.config_path)

    def test_create_default_config(self, tmp_path: Path):
        """测试创建默认配置。"""
        config_path = tmp_path / "test_config.yaml"
        manager = ConfigManager(config_path)
        
        manager.create_default_config()
        
        # 配置文件应该被创建
        assert config_path.exists()
        
        # 应该能够加载配置
        config = manager.load_config()
        assert isinstance(config, AppiumMCPConfig)

    def test_load_config_file_not_exists(self, tmp_path: Path):
        """测试加载不存在的配置文件。"""
        config_path = tmp_path / "nonexistent.yaml"
        manager = ConfigManager(config_path)
        
        # 应该返回默认配置
        config = manager.load_config()
        assert isinstance(config, AppiumMCPConfig)

    def test_load_config_with_valid_file(self, tmp_path: Path):
        """测试加载有效配置文件。"""
        config_path = tmp_path / "valid_config.yaml"
        config_content = """
server:
  host: "test-host"
  port: 5555
  timeout: 60

logging:
  level: "DEBUG"
  file: "test.log"
"""
        
        with open(config_path, "w") as f:
            f.write(config_content)
        
        manager = ConfigManager(config_path)
        config = manager.load_config()
        
        assert config.server.host == "test-host"
        assert config.server.port == 5555
        assert config.server.timeout == 60
        assert config.logging.level == "DEBUG"
        assert config.logging.file == "test.log"

    def test_load_config_with_invalid_yaml(self, tmp_path: Path):
        """测试加载无效YAML文件。"""
        config_path = tmp_path / "invalid.yaml"
        
        with open(config_path, "w") as f:
            f.write("invalid: yaml: content: [")
        
        manager = ConfigManager(config_path)
        
        with pytest.raises(ConfigurationError, match="Invalid YAML"):
            manager.load_config()

    def test_apply_env_overrides(self, tmp_path: Path):
        """测试环境变量覆盖。"""
        config_path = tmp_path / "test_config.yaml"
        manager = ConfigManager(config_path)
        
        with patch.dict(os.environ, {
            "APPIUM_MCP_SERVER_HOST": "env-host",
            "APPIUM_MCP_SERVER_PORT": "9999",
            "APPIUM_MCP_LOG_LEVEL": "ERROR",
        }):
            config = manager.load_config()
            
            assert config.server.host == "env-host"
            assert config.server.port == 9999
            assert config.logging.level == "ERROR"

    def test_save_config(self, tmp_path: Path):
        """测试保存配置。"""
        config_path = tmp_path / "save_test.yaml"
        manager = ConfigManager(config_path)
        
        config = AppiumMCPConfig()
        config.server.host = "saved-host"
        config.server.port = 7777
        
        manager.save_config(config)
        
        # 文件应该被创建
        assert config_path.exists()
        
        # 重新加载配置应该匹配
        loaded_config = manager.load_config()
        assert loaded_config.server.host == "saved-host"
        assert loaded_config.server.port == 7777

    def test_validate_config_valid(self):
        """测试验证有效配置。"""
        manager = ConfigManager()
        config = AppiumMCPConfig()
        
        result = manager.validate_config(config)
        assert result is True

    def test_validate_config_invalid(self):
        """测试验证无效配置。"""
        manager = ConfigManager()
        config = AppiumMCPConfig()
        
        # 设置无效端口
        config.server.port = 99999
        
        with pytest.raises(InvalidConfigError):
            manager.validate_config(config)

    def test_reload_config(self, tmp_path: Path):
        """测试重新加载配置。"""
        config_path = tmp_path / "reload_test.yaml"
        manager = ConfigManager(config_path)
        
        # 首次加载
        config1 = manager.load_config()
        assert config1.server.host == "localhost"
        
        # 修改配置文件
        config_content = """
server:
  host: "reloaded-host"
"""
        with open(config_path, "w") as f:
            f.write(config_content)
        
        # 重新加载
        config2 = manager.reload_config()
        assert config2.server.host == "reloaded-host"

    def test_get_config_not_loaded(self):
        """测试获取未加载的配置。"""
        manager = ConfigManager()
        
        with pytest.raises(ConfigurationError, match="Configuration not loaded"):
            manager.get_config()

    def test_convert_env_value(self, tmp_path: Path):
        """测试环境变量值转换。"""
        manager = ConfigManager(tmp_path / "test.yaml")
        
        # 测试布尔值转换
        assert manager._convert_env_value("true") is True
        assert manager._convert_env_value("false") is False
        assert manager._convert_env_value("1") is True
        assert manager._convert_env_value("0") is False
        
        # 测试数字转换
        assert manager._convert_env_value("123") == 123
        assert manager._convert_env_value("45.67") == 45.67
        
        # 测试字符串
        assert manager._convert_env_value("test") == "test"


@pytest.mark.unit
class TestConfigModels:
    """配置模型测试类。"""

    def test_server_config_validation(self):
        """测试服务器配置验证。"""
        from appium_mcp.core.config_manager import ServerConfig
        
        # 有效配置
        config = ServerConfig(port=4723)
        assert config.port == 4723
        
        # 无效端口
        with pytest.raises(ValueError, match="Port must be between"):
            ServerConfig(port=99999)
        
        # 无效超时
        with pytest.raises(ValueError, match="Timeout must be positive"):
            ServerConfig(timeout=-1)

    def test_logging_config_validation(self):
        """测试日志配置验证。"""
        from appium_mcp.core.config_manager import LoggingConfig
        
        # 有效配置
        config = LoggingConfig(level="DEBUG")
        assert config.level == "DEBUG"
        
        # 无效日志级别
        with pytest.raises(ValueError, match="Log level must be one of"):
            LoggingConfig(level="INVALID")

    def test_features_config_validation(self):
        """测试功能配置验证。"""
        from appium_mcp.core.config_manager import FeaturesConfig
        
        # 有效配置
        config = FeaturesConfig(screenshot_format="png")
        assert config.screenshot_format == "png"
        
        # 无效截图格式
        with pytest.raises(ValueError, match="Screenshot format must be"):
            FeaturesConfig(screenshot_format="invalid")
        
        # 无效录制质量
        with pytest.raises(ValueError, match="Recording quality must be"):
            FeaturesConfig(recording_quality="invalid") 