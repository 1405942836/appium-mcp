# 故障排除指南

本文档提供了 Appium MCP Server 常见问题的解决方案，帮助您快速诊断和解决问题。

## 🚨 MCP 连接问题

### 问题：Claude Desktop 显示红色指示灯

**症状**：
- Claude Desktop 中 appium 服务显示红色指示灯
- 无法调用 Appium 相关工具

**可能原因和解决方案**：

#### 1. MCP 服务器未启动或崩溃

```bash
# 检查服务器进程
tasklist | findstr appium-mcp-server  # Windows
ps aux | grep appium-mcp-server       # Linux/macOS

# 如果没有进程，重新启动
appium-mcp-server run
```

#### 2. 配置文件问题

```bash
# 检查配置文件
appium-mcp-server show-config

# 如果配置文件损坏，删除并使用默认配置
# Windows
del "%APPDATA%\appium-mcp\config.yaml"
# Linux/macOS
rm ~/.config/appium-mcp/config.yaml

# 重启服务器
appium-mcp-server run
```

#### 3. mcp.json 配置错误

检查 Claude Desktop 的 `mcp.json` 配置：

```json
{
  "mcpServers": {
    "appium": {
      "command": "appium-mcp-server",
      "args": ["run"]
    }
  }
}
```

**常见错误**：
- ❌ `"args": []` - 缺少 run 命令
- ❌ `"command": "appium-mcp"` - 命令名称错误
- ✅ `"command": "appium-mcp-server", "args": ["run"]` - 正确配置

#### 4. 权限问题

```bash
# Windows: 以管理员身份运行 Claude Desktop
# Linux/macOS: 检查执行权限
which appium-mcp-server
ls -la $(which appium-mcp-server)
```

#### 5. 重启 Claude Desktop

1. 完全退出 Claude Desktop
2. 等待 5 秒
3. 重新启动 Claude Desktop
4. 检查指示灯状态

## 🔧 配置相关问题

### 问题：配置文件生成不完整

**症状**：
```bash
PS> type config.yaml
android:
# 只有一行内容
```

**解决方案**：

1. **推荐方案**：使用内置默认配置
   ```bash
   # 删除损坏的配置文件
   del "%APPDATA%\appium-mcp\config.yaml"
   
   # 直接启动（使用内置默认配置）
   appium-mcp-server run
   ```

2. **手动创建配置文件**：
   参考 [配置指南](configuration.md) 中的完整配置示例

### 问题：CLI 命令格式错误

**常见错误命令**：
```bash
# ❌ 错误格式
appium-mcp-server config show
appium-mcp-server config validate

# ✅ 正确格式
appium-mcp-server show-config
appium-mcp-server validate-config
```

**解决方案**：
参考 [CLI 命令参考](cli-reference.md) 获取正确的命令格式。

## 📱 设备连接问题

### 问题：无法发现 Android 设备

**检查步骤**：

1. **验证 ADB 连接**：
   ```bash
   adb devices
   # 应该显示连接的设备
   ```

2. **重启 ADB 服务**：
   ```bash
   adb kill-server
   adb start-server
   adb devices
   ```

3. **检查 USB 调试**：
   - 确保设备开启了 USB 调试
   - 确认设备上的调试授权

4. **检查 Appium 服务器**：
   ```bash
   # 确保 Appium 服务器在运行
   curl http://localhost:4723/wd/hub/status
   ```

### 问题：iOS 设备发现失败（Windows）

**症状**：
```
ERROR: Failed to discover iOS devices: [WinError 2] 系统找不到指定的文件。
```

**解决方案**：
这是正常现象！Windows 系统不支持 iOS 设备连接，这个错误可以忽略。

## 🚀 服务器启动问题

### 问题：端口被占用

**症状**：
```
Error: Port 4723 is already in use
```

**解决方案**：

1. **检查端口占用**：
   ```bash
   # Windows
   netstat -ano | findstr :4723
   
   # Linux/macOS
   lsof -i :4723
   ```

2. **终止占用进程**：
   ```bash
   # Windows (替换 PID)
   taskkill /PID <PID> /F
   
   # Linux/macOS
   kill -9 <PID>
   ```

3. **使用不同端口**：
   ```bash
   # 启动 Appium 到不同端口
   appium --port 4724
   
   # 更新 MCP 服务器配置
   appium-mcp-server --config custom-config.yaml run
   ```

### 问题：Python 版本不兼容

**症状**：
```
ERROR: Python 3.8 is not supported. Please use Python 3.9+
```

**解决方案**：
1. 升级 Python 到 3.9 或更高版本
2. 使用虚拟环境：
   ```bash
   python3.9 -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   pip install appium-mcp-server
   ```

## 🔍 诊断工具

### 系统环境检查

```bash
# 运行系统诊断
appium-mcp-server doctor
```

这会检查：
- ✅ Python 版本
- ✅ 必需的 Python 包
- ✅ Appium 服务器状态
- ⚠️ 可选依赖

### 详细日志调试

```bash
# 启用调试日志
appium-mcp-server --log-level DEBUG run
```

### 配置验证

```bash
# 验证当前配置
appium-mcp-server validate-config

# 显示完整配置
appium-mcp-server show-config
```

## 🔄 Cursor 重启相关问题

### 问题：重启 Cursor 后服务停止

**回答您的问题**：

1. **是否需要重启 Cursor**：
   - 通常不需要重启 Cursor
   - 只有在修改了 `mcp.json` 配置后才需要重启 Claude Desktop

2. **重启 Cursor 对服务的影响**：
   - ✅ **Appium 服务器**：不会被 kill，因为它在独立的终端中运行
   - ❌ **MCP 服务器**：会被 kill，因为它是由 Claude Desktop 启动的子进程

3. **重启后的操作**：
   ```bash
   # 重启 Cursor 后，只需要确保 Appium 服务器还在运行
   curl http://localhost:4723/wd/hub/status
   
   # 如果 Appium 服务器停止了，重新启动
   appium --port 4723
   
   # MCP 服务器会由 Claude Desktop 自动启动
   ```

### 最佳实践

1. **保持 Appium 服务器独立运行**：
   ```bash
   # 在独立的终端窗口中运行
   appium --port 4723
   ```

2. **让 Claude Desktop 管理 MCP 服务器**：
   - 不要手动启动 MCP 服务器
   - 通过 `mcp.json` 配置让 Claude Desktop 自动管理

3. **推荐的工作流**：
   ```bash
   # 1. 启动 Appium（保持运行）
   appium --port 4723
   
   # 2. 启动 Claude Desktop（会自动启动 MCP 服务器）
   # 3. 可以随时重启 Cursor，不影响 Appium 服务器
   ```

## 📞 获取更多帮助

如果以上解决方案都无法解决您的问题：

1. **查看日志**：
   ```bash
   appium-mcp-server --log-level DEBUG run
   ```

2. **收集诊断信息**：
   ```bash
   appium-mcp-server doctor > diagnosis.txt
   appium-mcp-server show-config >> diagnosis.txt
   ```

3. **提交 Issue**：
   - 包含完整的错误信息
   - 附上诊断信息
   - 说明操作系统和版本
   - 描述重现步骤

---

> 💡 **提示**: 大多数问题都可以通过删除配置文件并使用默认配置来解决。如果遇到问题，首先尝试使用内置默认配置。