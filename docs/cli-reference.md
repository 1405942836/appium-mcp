# CLI 命令参考

Appium MCP Server 提供了丰富的命令行工具，用于服务器管理、配置管理和系统诊断。

## 📋 命令总览

```bash
appium-mcp-server [全局选项] <命令> [命令选项]
```

### 全局选项

| 选项 | 描述 | 默认值 |
|------|------|--------|
| `--version` | 显示版本信息并退出 | - |
| `-c, --config PATH` | 指定配置文件路径 | 自动检测 |
| `-l, --log-level LEVEL` | 设置日志级别 | INFO |
| `--help` | 显示帮助信息并退出 | - |

**日志级别选项**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## 🚀 核心命令

### `run` - 启动服务器

启动 MCP 服务器（stdio 模式）。

```bash
# 基本启动
appium-mcp-server run

# 使用指定配置文件启动
appium-mcp-server --config /path/to/config.yaml run

# 使用调试日志级别启动
appium-mcp-server --log-level DEBUG run
```

**特点**：
- ✅ 自动加载默认位置的配置文件（如果存在）
- ✅ 支持 Ctrl+C 优雅停止
- ✅ 实时显示服务器状态

### `init-config` - 生成配置文件

生成默认配置文件到指定位置。

```bash
# 生成到默认位置
appium-mcp-server init-config

# 生成到指定位置
appium-mcp-server --config /custom/path/config.yaml init-config
```

**⚠️ 已知问题**: 当前版本存在配置文件生成不完整的Bug，建议使用内置默认配置。

## ⚙️ 配置管理命令

### `show-config` - 显示当前配置

显示当前加载的完整配置信息。

```bash
# 显示默认配置
appium-mcp-server show-config

# 显示指定配置文件的配置
appium-mcp-server --config /path/to/config.yaml show-config
```

**输出格式**: JSON格式，包含所有配置项和当前值

### `validate-config` - 验证配置文件

验证配置文件的语法和有效性。

```bash
# 验证默认配置
appium-mcp-server validate-config

# 验证指定配置文件
appium-mcp-server --config /path/to/config.yaml validate-config
```

**验证内容**：
- YAML 语法正确性
- 配置项有效性
- 端口冲突检查
- 路径有效性检查

## 🔍 诊断命令

### `doctor` - 系统环境检查

检查系统环境和依赖项是否正确安装。

```bash
appium-mcp-server doctor
```

**检查项目**：
- ✅ Python 版本
- ✅ 必需的 Python 包
- ✅ Appium 服务器状态
- ⚠️ 可选依赖（如 Xcode Command Line Tools）

### `status` - 服务器状态

显示服务器运行状态（需要服务器正在运行）。

```bash
appium-mcp-server status
```

**显示信息**：
- 服务器运行状态
- 活动连接数
- 设备连接状态
- 资源使用情况

### `version` - 版本信息

显示详细的版本信息。

```bash
appium-mcp-server version
```

**包含信息**：
- 服务器版本
- 依赖包版本
- Python 版本
- 系统信息

## 📱 设备管理命令

### `list-devices` - 列出可用设备

列出所有可用的移动设备（需要 Appium 服务器运行）。

```bash
appium-mcp-server list-devices
```

**显示信息**：
- 设备 ID
- 设备名称
- 平台类型
- 连接状态

## 📝 使用示例

### 完整启动流程

```bash
# 1. 检查环境
appium-mcp-server doctor

# 2. 验证配置（可选）
appium-mcp-server validate-config

# 3. 启动服务器
appium-mcp-server run
```

### 调试模式启动

```bash
# 启用详细日志
appium-mcp-server --log-level DEBUG run

# 使用自定义配置
appium-mcp-server --config ./debug-config.yaml --log-level DEBUG run
```

### 配置管理工作流

```bash
# 1. 生成配置文件模板
appium-mcp-server init-config

# 2. 编辑配置文件
# 使用文本编辑器编辑 %APPDATA%\appium-mcp\config.yaml

# 3. 验证配置
appium-mcp-server validate-config

# 4. 查看最终配置
appium-mcp-server show-config

# 5. 启动服务器
appium-mcp-server run
```

## 🚨 故障排除

### 常见错误和解决方案

#### 1. "No such command" 错误

```bash
# ❌ 错误用法
appium-mcp-server config show

# ✅ 正确用法
appium-mcp-server show-config
```

#### 2. 配置文件路径问题

```bash
# 检查配置文件是否存在
appium-mcp-server show-config

# 如果配置文件损坏，删除并重新生成
# Windows
del "%APPDATA%\appium-mcp\config.yaml"
appium-mcp-server init-config
```

#### 3. 权限问题

```bash
# Windows: 以管理员身份运行
# Linux/macOS: 检查文件权限
chmod 644 ~/.config/appium-mcp/config.yaml
```

## 🔧 高级用法

### 环境变量配置

```bash
# 设置环境变量
set APPIUM_MCP_SERVER_PORT=5000
set APPIUM_MCP_LOG_LEVEL=DEBUG

# 启动服务器（会应用环境变量）
appium-mcp-server run
```

### 批处理脚本

```batch
@echo off
echo 启动 Appium MCP Server...

REM 检查环境
appium-mcp-server doctor
if errorlevel 1 (
    echo 环境检查失败，请检查依赖安装
    pause
    exit /b 1
)

REM 启动服务器
appium-mcp-server run
```

## 📚 相关文档

- [配置指南](configuration.md) - 详细的配置选项说明
- [故障排除](troubleshooting.md) - 常见问题解决方案
- [快速开始](quickstart.md) - 快速上手指南

---

> 💡 **提示**: 所有命令都支持 `--help` 选项，可以查看详细的命令帮助信息。