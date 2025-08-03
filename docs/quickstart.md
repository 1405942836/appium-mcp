# 快速开始

本文档将帮助您在5分钟内快速上手Appium MCP服务器，从安装到运行第一个自动化测试。

## ⚡ 快速安装

### 前提条件检查

```bash
# 检查Python版本 (需要 >= 3.9)
python --version

# 检查Node.js版本 (需要 >= 16.0)
node --version

# 检查Java版本 (需要 >= JDK 8)
java -version
```

### 一键安装脚本

```bash
# 下载并运行安装脚本
curl -sSL https://raw.githubusercontent.com/your-repo/appium-mcp/main/scripts/quick-install.sh | bash

# 或者手动安装
pip install appium-mcp-server
npm install -g appium
appium driver install uiautomator2
```

## 🚀 第一次运行

### 1. 启动Appium服务器

```bash
# 在终端1中启动Appium服务器
appium --port 4723
```

### 2. 连接Android设备

```bash
# 连接Android设备或启动模拟器
adb devices

# 如果没有设备，创建并启动模拟器
avdmanager create avd -n test_device -k "system-images;android-30;google_apis;x86_64"
emulator -avd test_device
```

### 3. 启动MCP服务器

```bash
# 在终端2中启动MCP服务器
appium-mcp-server

# 或指定配置文件
appium-mcp-server --config ~/.config/appium-mcp/config.yaml
```

## 📱 第一个自动化测试

### 使用Claude Desktop

1. **配置MCP连接**

在Claude Desktop的设置中添加：

```json
{
  "mcpServers": {
    "appium": {
      "command": "appium-mcp-server",
      "args": []
    }
  }
}
```

2. **重启Claude Desktop**

3. **开始测试对话**

```
你好！请帮我连接Android设备，然后打开设置应用并截图。
```

### 使用Python客户端

创建 `test_client.py` 文件：

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # 连接MCP服务器
    server_params = StdioServerParameters(
        command="appium-mcp-server",
        args=[]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            
            # 1. 列出可用设备
            result = await session.call_tool("list_devices", {})
            print("可用设备:", result.content[0].text)
            
            # 2. 连接第一个设备
            result = await session.call_tool("connect_device", {
                "device_id": "emulator-5554"  # 替换为实际设备ID
            })
            print("连接结果:", result.content[0].text)
            
            # 3. 启动设置应用
            result = await session.call_tool("launch_app", {
                "device_id": "emulator-5554",
                "app_package": "com.android.settings",
                "app_activity": ".Settings"
            })
            print("应用启动:", result.content[0].text)
            
            # 4. 截图
            result = await session.call_tool("take_screenshot", {
                "device_id": "emulator-5554"
            })
            print("截图完成:", result.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
```

运行测试：

```bash
python test_client.py
```

## 🎯 常用操作示例

### 设备操作

```python
# 列出所有设备
await session.call_tool("list_devices", {})

# 获取设备信息
await session.call_tool("get_device_info", {
    "device_id": "emulator-5554"
})

# 安装应用
await session.call_tool("install_app", {
    "device_id": "emulator-5554",
    "app_path": "/path/to/app.apk"
})
```

### UI交互

```python
# 查找元素
await session.call_tool("find_element", {
    "device_id": "emulator-5554",
    "locator_type": "id",
    "locator_value": "com.android.settings:id/search_button"
})

# 点击元素
await session.call_tool("click_element", {
    "device_id": "emulator-5554",
    "element_id": "element-123"
})

# 输入文本
await session.call_tool("input_text", {
    "device_id": "emulator-5554",
    "element_id": "element-456",
    "text": "Hello World"
})
```

### 手势操作

```python
# 滑动
await session.call_tool("swipe", {
    "device_id": "emulator-5554",
    "start_x": 500,
    "start_y": 1000,
    "end_x": 500,
    "end_y": 300,
    "duration": 1000
})

# 截图
await session.call_tool("take_screenshot", {
    "device_id": "emulator-5554",
    "save_path": "/tmp/screenshot.png"
})
```

## 🔧 配置文件

### 创建配置文件

```bash
# 生成默认配置
appium-mcp-server init-config
```

### 配置示例

```yaml
# ~/.config/appium-mcp/config.yaml
server:
  host: "localhost"
  port: 4723
  timeout: 30
  
devices:
  android:
    platform_name: "Android"
    automation_name: "UiAutomator2"
    device_name: "Android Emulator"
    
  ios:
    platform_name: "iOS"
    automation_name: "XCUITest"
    device_name: "iPhone Simulator"

logging:
  level: "INFO"
  file: "appium-mcp.log"
  
features:
  auto_screenshot: true
  element_highlight: true
  performance_logging: true
```

## 📊 验证安装

### 运行健康检查

```bash
# 系统健康检查
appium-mcp-server doctor

# 检查设备连接
appium-mcp-server devices

# 测试工具调用
appium-mcp-server test-tools
```

### 预期输出

```
✅ Python环境: 3.11.0
✅ Appium服务器: 2.0.0
✅ Android SDK: 已配置
✅ 设备连接: 1个设备已连接
✅ MCP服务器: 运行正常
✅ 工具注册: 40个工具可用
```

## 🐛 快速故障排除

### 常见问题

1. **设备未找到**
   ```bash
   # 检查ADB连接
   adb devices
   
   # 重启ADB服务
   adb kill-server && adb start-server
   ```

2. **端口被占用**
   ```bash
   # 查找占用进程
   lsof -i :4723
   
   # 使用其他端口
   appium-mcp-server --port 4724
   ```

3. **权限问题**
   ```bash
   # Android开发者选项
   # 启用USB调试和USB安装
   
   # iOS信任开发者证书
   ```

### 获取帮助

```bash
# 查看详细日志
appium-mcp-server --log-level debug

# 生成诊断报告
appium-mcp-server diagnose > diagnosis.txt
```

## 🎉 下一步

恭喜！您已经成功运行了第一个Appium MCP自动化测试。

### 继续学习

- 📖 [工具参考](tools/README.md) - 了解所有可用工具
- 🏗️ [架构设计](architecture.md) - 深入理解系统架构
- 📝 [使用示例](examples/README.md) - 更多实际使用场景
- ⚙️ [配置指南](configuration.md) - 高级配置选项

### 加入社区

- 🐛 [报告问题](https://github.com/your-repo/appium-mcp/issues)
- 💬 [参与讨论](https://github.com/your-repo/appium-mcp/discussions)
- 📚 [贡献文档](CONTRIBUTING.md)

---

> 🎯 **目标达成**: 您现在已经掌握了Appium MCP服务器的基本使用方法，可以开始构建自己的自动化测试流程了！ 