# 开发测试指南

本文档介绍如何测试开发中的 Appium MCP Server 项目。

## 🎯 适用场景

- 本地开发环境测试
- 项目功能验证
- 集成测试
- 发布前验证

## 📋 前置条件

### 系统要求
- Python 3.9+
- Node.js 16+ (用于 Appium)
- Git

### 环境检查
```bash
# 检查 Python 版本
python --version

# 检查 Node.js 版本  
node --version

# 检查项目结构
ls src/appium_mcp/
```

## 🚀 快速测试流程

### 步骤1：环境准备

```bash
# 1. 克隆项目（如果需要）
git clone <repository-url>
cd appium-mcp

# 2. 激活虚拟环境
# Windows
.\.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate

# 3. 安装开发依赖
pip install -e .
```

### 步骤2：基础验证

```bash
# 运行简单测试
python simple_test.py

# 运行项目验证脚本
# Windows
.\verify_project.bat
# PowerShell
.\Verify-Project.ps1
```

### 步骤3：单元测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行所有单元测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/unit/test_config_manager.py -v
```

### 步骤4：集成测试

```bash
# 运行集成测试套件
python test_runner.py

# 手动测试 MCP 服务器
python -c "from src.appium_mcp import AppiumMCPServer; print('✅ 导入成功')"
```

## 🧪 详细测试步骤

### 1. 模块导入测试

```python
# 测试核心模块导入
from src.appium_mcp import AppiumMCPServer
from src.appium_mcp.core.config_manager import ConfigManager
from src.appium_mcp.tools.device_tools import ListDevicesTool
```

### 2. 配置管理测试

```python
# 测试配置加载
config_manager = ConfigManager()
config = config_manager.load_config()
print(f"配置加载成功: {config}")
```

### 3. MCP 服务器测试

```bash
# 测试服务器启动（需要 Appium 运行）
python -c "
import asyncio
from src.appium_mcp.server import AppiumMCPServer

async def test():
    server = AppiumMCPServer()
    await server.initialize()
    print('✅ 服务器初始化成功')

asyncio.run(test())
"
```

### 4. 工具功能测试

```python
# 测试工具注册
from src.appium_mcp.tools.device_tools import ListDevicesTool
from src.appium_mcp.core.session_manager import SessionManager

session_manager = SessionManager("http://localhost:4723")
tool = ListDevicesTool(session_manager)
print(f"工具名称: {tool.name}")
```

## 🔧 开发环境配置

### 配置 IDE

**VS Code / Cursor 配置**：
```json
{
  "python.defaultInterpreterPath": "./.venv/Scripts/python.exe",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"]
}
```

### 本地 MCP 测试

如果要在 Cursor 中测试 MCP 连接，有以下几种最佳实践：

#### 方案1：使用虚拟环境中的 Python（推荐）

```json
{
  "mcpServers": {
    "appium-dev": {
      "command": "D:/Projects/github/appium-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "src.appium_mcp.cli", "run"],
      "cwd": "D:/Projects/github/appium-mcp",
      "env": {}
    }
  }
}
```

#### 方案2：使用批处理脚本（Windows 推荐）

创建 `start-mcp-dev.bat` 文件：
```batch
@echo off
cd /d "D:\Projects\github\appium-mcp"
call .venv\Scripts\activate.bat
python -m src.appium_mcp.cli run
```

然后在 MCP 配置中：
```json
{
  "mcpServers": {
    "appium-dev": {
      "command": "D:/Projects/github/appium-mcp/start-mcp-dev.bat",
      "args": [],
      "cwd": "D:/Projects/github/appium-mcp"
    }
  }
}
```

#### 方案3：使用 PowerShell 脚本

创建 `start-mcp-dev.ps1` 文件：
```powershell
Set-Location "D:\Projects\github\appium-mcp"
& ".\.venv\Scripts\Activate.ps1"
python -m src.appium_mcp.cli run
```

然后在 MCP 配置中：
```json
{
  "mcpServers": {
    "appium-dev": {
      "command": "powershell.exe",
      "args": ["-ExecutionPolicy", "Bypass", "-File", "start-mcp-dev.ps1"],
      "cwd": "D:/Projects/github/appium-mcp"
    }
  }
}
```

#### 方案4：设置环境变量（跨平台）

```json
{
  "mcpServers": {
    "appium-dev": {
      "command": "D:/Projects/github/appium-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "src.appium_mcp.cli", "run"],
      "cwd": "D:/Projects/github/appium-mcp",
      "env": {
        "PYTHONPATH": "D:/Projects/github/appium-mcp/src",
        "PATH": "D:/Projects/github/appium-mcp/.venv/Scripts;%PATH%"
      }
    }
  }
}
```

### 🎯 推荐配置

**Windows 开发环境推荐使用方案1或方案2**，因为：
- 明确指定虚拟环境中的 Python 解释器
- 避免全局 Python 环境的干扰
- 确保使用正确的依赖包版本

## 🚨 常见问题

### 1. 导入错误
```
ModuleNotFoundError: No module named 'src.appium_mcp'
```

**解决方案**：
```bash
# 确保在项目根目录
pwd
# 安装为可编辑包
pip install -e .
```

### 2. 依赖缺失
```
ImportError: No module named 'mcp'
```

**解决方案**：
```bash
# 安装所有依赖
pip install -e .
# 或手动安装
pip install mcp pydantic pyyaml click structlog
```

### 3. Appium 连接失败
```
ConnectionError: Unable to connect to Appium server
```

**解决方案**：
```bash
# 启动 Appium 服务器
appium --port 4723
# 检查连接
curl http://localhost:4723/wd/hub/status
```

## 📊 测试检查清单

### 基础测试
- [ ] Python 环境正确 (3.9+)
- [ ] 虚拟环境激活
- [ ] 项目依赖安装完成
- [ ] 核心模块可以导入

### 功能测试  
- [ ] 配置管理器工作正常
- [ ] MCP 服务器可以初始化
- [ ] 工具可以正确注册
- [ ] 资源管理器功能正常

### 集成测试
- [ ] 与 Appium 服务器连接正常
- [ ] MCP 协议通信正常
- [ ] 工具执行功能正常
- [ ] 错误处理机制正常

### 发布前测试
- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] 文档测试示例可用
- [ ] 包安装测试成功

## 🎯 测试最佳实践

1. **环境隔离**: 始终在虚拟环境中测试
2. **增量测试**: 从简单到复杂逐步测试
3. **自动化**: 使用提供的脚本进行自动化测试
4. **日志记录**: 保留测试日志用于问题诊断
5. **清理环境**: 测试后清理临时文件

## 📞 获取帮助

如果测试过程中遇到问题：

1. 查看 [故障排除文档](troubleshooting.md)
2. 检查项目 Issues
3. 运行诊断脚本：`python simple_test.py`
4. 查看详细日志输出

---

> 💡 **提示**: 建议在每次代码修改后运行 `python simple_test.py` 进行快速验证。