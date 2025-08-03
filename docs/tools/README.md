# 工具参考

本文档详细介绍Appium MCP服务器提供的所有工具。工具按功能分类，每个工具都包含详细的参数说明和使用示例。

## 🗂️ 工具分类

### 📱 设备管理工具 (Device Management)
用于设备发现、连接和基本信息获取。

| 工具名称 | 描述 | 平台支持 |
|----------|------|----------|
| [list_devices](device-management.md#list_devices) | 列出所有可用设备 | Android, iOS |
| [connect_device](device-management.md#connect_device) | 连接指定设备 | Android, iOS |
| [disconnect_device](device-management.md#disconnect_device) | 断开设备连接 | Android, iOS |
| [get_device_info](device-management.md#get_device_info) | 获取设备详细信息 | Android, iOS |
| [get_device_status](device-management.md#get_device_status) | 获取设备状态 | Android, iOS |
| [install_app](device-management.md#install_app) | 安装应用到设备 | Android, iOS |
| [uninstall_app](device-management.md#uninstall_app) | 从设备卸载应用 | Android, iOS |
| [get_installed_apps](device-management.md#get_installed_apps) | 获取已安装应用列表 | Android, iOS |

### 🎯 UI自动化工具 (UI Automation)
用于UI元素查找、交互和手势操作。

| 工具名称 | 描述 | 平台支持 |
|----------|------|----------|
| [find_element](ui-automation.md#find_element) | 查找单个UI元素 | Android, iOS |
| [find_elements](ui-automation.md#find_elements) | 查找多个UI元素 | Android, iOS |
| [click_element](ui-automation.md#click_element) | 点击UI元素 | Android, iOS |
| [input_text](ui-automation.md#input_text) | 输入文本到元素 | Android, iOS |
| [clear_text](ui-automation.md#clear_text) | 清除元素文本 | Android, iOS |
| [get_element_text](ui-automation.md#get_element_text) | 获取元素文本内容 | Android, iOS |
| [get_element_attribute](ui-automation.md#get_element_attribute) | 获取元素属性 | Android, iOS |
| [swipe](ui-automation.md#swipe) | 执行滑动手势 | Android, iOS |
| [scroll](ui-automation.md#scroll) | 执行滚动操作 | Android, iOS |
| [drag_and_drop](ui-automation.md#drag_and_drop) | 拖拽操作 | Android, iOS |
| [multi_touch](ui-automation.md#multi_touch) | 多点触控手势 | Android, iOS |
| [get_screen_size](ui-automation.md#get_screen_size) | 获取屏幕尺寸 | Android, iOS |

### 🚀 应用控制工具 (App Control)
用于应用生命周期管理和状态控制。

| 工具名称 | 描述 | 平台支持 |
|----------|------|----------|
| [launch_app](app-control.md#launch_app) | 启动应用 | Android, iOS |
| [close_app](app-control.md#close_app) | 关闭应用 | Android, iOS |
| [background_app](app-control.md#background_app) | 将应用置于后台 | Android, iOS |
| [activate_app](app-control.md#activate_app) | 激活应用到前台 | Android, iOS |
| [terminate_app](app-control.md#terminate_app) | 终止应用进程 | Android, iOS |
| [get_app_state](app-control.md#get_app_state) | 获取应用状态 | Android, iOS |

### ⚙️ 系统操作工具 (System Operations)
用于系统级操作和设备控制。

| 工具名称 | 描述 | 平台支持 |
|----------|------|----------|
| [take_screenshot](system-operations.md#take_screenshot) | 截取屏幕截图 | Android, iOS |
| [start_recording](system-operations.md#start_recording) | 开始录制屏幕 | Android, iOS |
| [stop_recording](system-operations.md#stop_recording) | 停止录制屏幕 | Android, iOS |
| [press_key](system-operations.md#press_key) | 按键操作 | Android, iOS |
| [press_keycode](system-operations.md#press_keycode) | 按键码操作 | Android |
| [long_press_keycode](system-operations.md#long_press_keycode) | 长按键码 | Android |
| [rotate_device](system-operations.md#rotate_device) | 旋转设备 | Android, iOS |
| [set_orientation](system-operations.md#set_orientation) | 设置屏幕方向 | Android, iOS |
| [get_orientation](system-operations.md#get_orientation) | 获取屏幕方向 | Android, iOS |
| [shake_device](system-operations.md#shake_device) | 摇晃设备 | iOS |

### 📁 文件操作工具 (File Operations)
用于设备文件系统的操作。

| 工具名称 | 描述 | 平台支持 |
|----------|------|----------|
| [push_file](file-operations.md#push_file) | 推送文件到设备 | Android, iOS |
| [pull_file](file-operations.md#pull_file) | 从设备拉取文件 | Android, iOS |
| [list_files](file-operations.md#list_files) | 列出设备文件 | Android |
| [delete_file](file-operations.md#delete_file) | 删除设备文件 | Android |

## 🎛️ 工具使用模式

### 1. 基本调用模式

```python
# MCP客户端调用示例
result = await client.call_tool("list_devices", {})
```

### 2. 参数验证

所有工具都使用Pydantic进行参数验证：

```python
from pydantic import BaseModel

class ListDevicesArgs(BaseModel):
    platform: Optional[str] = None  # "android" | "ios" | None
    status: Optional[str] = None    # "connected" | "available" | None
```

### 3. 错误处理

工具执行可能返回错误信息：

```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "Device not found: emulator-5554"
    }
  ]
}
```

## 📊 工具统计

| 分类 | 工具数量 | 覆盖平台 | 主要用途 |
|------|----------|----------|----------|
| 设备管理 | 8个 | Android, iOS | 设备发现和连接 |
| UI自动化 | 12个 | Android, iOS | 界面交互操作 |
| 应用控制 | 6个 | Android, iOS | 应用生命周期 |
| 系统操作 | 10个 | Android, iOS | 系统级控制 |
| 文件操作 | 4个 | 主要Android | 文件系统操作 |
| **总计** | **40个** | - | - |

## 🔍 快速查找

### 按功能查找

| 我想要... | 使用工具 |
|-----------|----------|
| 连接设备 | [connect_device](device-management.md#connect_device) |
| 启动应用 | [launch_app](app-control.md#launch_app) |
| 点击按钮 | [click_element](ui-automation.md#click_element) |
| 输入文字 | [input_text](ui-automation.md#input_text) |
| 截取屏幕 | [take_screenshot](system-operations.md#take_screenshot) |
| 滑动屏幕 | [swipe](ui-automation.md#swipe) |
| 传输文件 | [push_file](file-operations.md#push_file) |

### 按平台查找

| 平台 | 专有工具 | 通用工具 |
|------|----------|----------|
| Android | press_keycode, list_files | 其他所有工具 |
| iOS | shake_device | 其他所有工具 |
| 通用 | - | 大部分工具 |

## 📚 详细文档

点击以下链接查看各类工具的详细文档：

- [设备管理工具详解](device-management.md)
- [UI自动化工具详解](ui-automation.md)
- [应用控制工具详解](app-control.md)
- [系统操作工具详解](system-operations.md)
- [文件操作工具详解](file-operations.md)

## 🔧 工具开发

如需开发自定义工具，请参考：
- [扩展开发指南](../development.md)
- [工具开发API](../api/tools.md)

---

> 💡 **提示**: 建议先从设备管理工具开始，建立设备连接后再使用其他功能工具。每个工具都有完整的参数验证和错误处理。 