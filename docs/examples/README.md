# 使用示例

本文档提供了Appium MCP服务器的实际使用场景示例，涵盖从基础操作到复杂自动化测试的各种用例。

## 📚 示例分类

### 🚀 基础示例
适合初学者，展示基本功能的使用方法。

| 示例 | 描述 | 难度 |
|------|------|------|
| [设备连接](basic/device-connection.md) | 连接和管理设备 | ⭐ |
| [应用启动](basic/app-launch.md) | 启动和关闭应用 | ⭐ |
| [元素查找](basic/element-finding.md) | 查找和操作UI元素 | ⭐ |
| [基础交互](basic/basic-interactions.md) | 点击、输入、滑动等基础操作 | ⭐ |
| [截图录屏](basic/screenshot-recording.md) | 截图和屏幕录制 | ⭐ |

### 🎯 实用场景
常见的自动化测试场景和最佳实践。

| 示例 | 描述 | 难度 |
|------|------|------|
| [登录流程](scenarios/login-flow.md) | 自动化登录测试 | ⭐⭐ |
| [表单填写](scenarios/form-filling.md) | 表单自动填写和验证 | ⭐⭐ |
| [列表操作](scenarios/list-operations.md) | 列表滚动、搜索、筛选 | ⭐⭐ |
| [多页面导航](scenarios/multi-page-navigation.md) | 页面间导航和状态保持 | ⭐⭐ |
| [文件上传下载](scenarios/file-operations.md) | 文件传输和管理 | ⭐⭐ |

### 🏗️ 高级应用
复杂的测试场景和高级功能应用。

| 示例 | 描述 | 难度 |
|------|------|------|
| [多设备协同](advanced/multi-device.md) | 多设备并行测试 | ⭐⭐⭐ |
| [性能测试](advanced/performance-testing.md) | 性能监控和测试 | ⭐⭐⭐ |
| [AI辅助测试](advanced/ai-assisted-testing.md) | 结合AI的智能测试 | ⭐⭐⭐ |
| [自定义工具](advanced/custom-tools.md) | 开发自定义测试工具 | ⭐⭐⭐ |
| [CI/CD集成](advanced/cicd-integration.md) | 持续集成和部署 | ⭐⭐⭐ |

### 🎨 创意应用
展示MCP服务器的创新使用方式。

| 示例 | 描述 | 难度 |
|------|------|------|
| [游戏自动化](creative/game-automation.md) | 手机游戏自动化 | ⭐⭐⭐ |
| [设备农场](creative/device-farm.md) | 构建设备测试农场 | ⭐⭐⭐ |
| [无障碍测试](creative/accessibility-testing.md) | 无障碍功能测试 | ⭐⭐ |
| [跨平台测试](creative/cross-platform.md) | Android和iOS统一测试 | ⭐⭐⭐ |

## 🔧 示例使用方法

### 1. 环境准备

每个示例都假设您已经完成了基本安装：

```bash
# 确保环境就绪
appium-mcp-server doctor

# 检查设备连接
adb devices  # Android
xcrun simctl list devices  # iOS
```

### 2. 运行示例

```bash
# 克隆示例代码
git clone https://github.com/your-repo/appium-mcp-examples.git
cd appium-mcp-examples

# 安装依赖
pip install -r requirements.txt

# 运行特定示例
python examples/basic/device_connection.py
```

### 3. 自定义示例

所有示例都可以根据您的需求进行修改：

```python
# 修改设备ID
DEVICE_ID = "your-device-id"

# 修改应用包名
APP_PACKAGE = "your.app.package"

# 修改测试数据
TEST_DATA = {
    "username": "your-username",
    "password": "your-password"
}
```

## 📱 平台特定示例

### Android示例

```python
# Android特有功能示例
await session.call_tool("press_keycode", {
    "device_id": "emulator-5554",
    "keycode": 4  # 返回键
})

await session.call_tool("list_files", {
    "device_id": "emulator-5554",
    "path": "/sdcard/Download"
})
```

### iOS示例

```python
# iOS特有功能示例
await session.call_tool("shake_device", {
    "device_id": "iPhone-Simulator"
})

# iOS应用启动
await session.call_tool("launch_app", {
    "device_id": "iPhone-Simulator",
    "bundle_id": "com.apple.mobilesafari"
})
```

## 🎭 与AI助手的对话示例

### Claude Desktop对话

```
用户: 请帮我测试一个购物应用的登录功能

助手: 我来帮您测试购物应用的登录功能。让我先检查设备连接情况，然后启动应用进行测试。

[调用 list_devices 工具]
[调用 connect_device 工具]
[调用 launch_app 工具]
[调用 find_element 工具查找用户名输入框]
[调用 input_text 工具输入用户名]
[调用 find_element 工具查找密码输入框]
[调用 input_text 工具输入密码]
[调用 click_element 工具点击登录按钮]
[调用 take_screenshot 工具截图验证]

测试完成！登录功能正常，用户已成功登录到应用主页。
```

### ChatGPT对话

```
用户: 我需要批量测试多个设备上的应用安装

助手: 我将帮您实现多设备并行的应用安装测试。

首先获取所有可用设备：
[调用 list_devices]

然后为每个设备并行执行：
1. 连接设备
2. 安装应用
3. 验证安装结果
4. 截图记录

让我开始执行这个批量测试流程...
```

## 🔍 示例索引

### 按功能分类

| 功能类别 | 相关示例 |
|----------|----------|
| 设备管理 | [设备连接](basic/device-connection.md), [多设备协同](advanced/multi-device.md) |
| 应用控制 | [应用启动](basic/app-launch.md), [登录流程](scenarios/login-flow.md) |
| UI交互 | [元素查找](basic/element-finding.md), [表单填写](scenarios/form-filling.md) |
| 手势操作 | [基础交互](basic/basic-interactions.md), [游戏自动化](creative/game-automation.md) |
| 文件操作 | [文件上传下载](scenarios/file-operations.md) |
| 系统功能 | [截图录屏](basic/screenshot-recording.md), [性能测试](advanced/performance-testing.md) |

### 按平台分类

| 平台 | 专用示例 | 通用示例 |
|------|----------|----------|
| Android | [Android专用功能](platform/android-specific.md) | 其他所有示例 |
| iOS | [iOS专用功能](platform/ios-specific.md) | 其他所有示例 |
| 跨平台 | [跨平台测试](creative/cross-platform.md) | 大部分示例 |

### 按复杂度分类

| 难度 | 示例数量 | 适合人群 |
|------|----------|----------|
| ⭐ 初级 | 5个 | 新手入门 |
| ⭐⭐ 中级 | 8个 | 有一定经验 |
| ⭐⭐⭐ 高级 | 7个 | 专业开发者 |

## 📋 示例模板

### 基础示例模板

```python
"""
示例名称: [示例名称]
描述: [简短描述]
难度: ⭐/⭐⭐/⭐⭐⭐
平台: Android/iOS/通用
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    """主函数"""
    server_params = StdioServerParameters(
        command="appium-mcp-server",
        args=[]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 示例代码
            print("开始执行示例...")
            
            # 1. 第一步操作
            result = await session.call_tool("tool_name", {
                "param": "value"
            })
            print(f"步骤1结果: {result.content[0].text}")
            
            # 2. 第二步操作
            # ...
            
            print("示例执行完成！")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🚀 贡献示例

我们欢迎社区贡献新的示例！

### 贡献步骤

1. Fork项目仓库
2. 创建示例分支
3. 编写示例代码和文档
4. 提交Pull Request

### 示例要求

- 代码清晰易懂，有详细注释
- 包含完整的使用说明
- 提供预期输出示例
- 标注适用的平台和难度

---

> 💡 **提示**: 建议从基础示例开始学习，逐步提高到高级应用。每个示例都可以作为您项目的起点进行修改和扩展。 