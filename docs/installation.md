# 安装指南

本文档详细介绍如何安装和配置Appium MCP服务器。

## 🎯 系统要求

### 最低要求
- **操作系统**: Windows 10+, macOS 10.15+, Linux Ubuntu 18.04+
- **Python版本**: 3.9+
- **内存**: 4GB RAM
- **存储空间**: 2GB 可用空间

### 推荐配置
- **操作系统**: Windows 11, macOS 13+, Linux Ubuntu 22.04+
- **Python版本**: 3.11+
- **内存**: 8GB+ RAM
- **存储空间**: 5GB+ 可用空间
- **CPU**: 4核心以上

## 📋 前置依赖

### 1. Python环境

```bash
# 检查Python版本
python --version  # 需要 >= 3.9

# 或使用python3
python3 --version
```

### 2. Node.js和npm (用于Appium)

```bash
# 安装Node.js (推荐使用LTS版本)
# 方式1: 官网下载安装 https://nodejs.org/

# 方式2: 使用包管理器
# macOS
brew install node

# Ubuntu/Debian
sudo apt install nodejs npm

# Windows (使用Chocolatey)
choco install nodejs
```

### 3. Java Development Kit (JDK)

Android开发需要JDK支持:

```bash
# 检查Java版本
java -version  # 需要 >= JDK 8

# macOS安装
brew install openjdk@11

# Ubuntu/Debian安装
sudo apt install openjdk-11-jdk

# Windows安装
# 下载并安装Oracle JDK或OpenJDK
```

## 🤖 Android环境配置

### 1. Android SDK安装

```bash
# 方式1: 安装Android Studio (推荐)
# 下载地址: https://developer.android.com/studio

# 方式2: 仅安装SDK命令行工具
# 下载地址: https://developer.android.com/studio/command-line
```

### 2. 环境变量配置

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc (macOS/Linux)
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin

# Windows环境变量设置
# ANDROID_HOME: C:\Users\%USERNAME%\AppData\Local\Android\Sdk
# PATH添加: %ANDROID_HOME%\platform-tools;%ANDROID_HOME%\emulator
```

### 3. ADB验证

```bash
# 重新加载环境变量
source ~/.bashrc  # Linux/macOS

# 验证ADB
adb version

# 检查连接的设备
adb devices
```

## 🍎 iOS环境配置 (仅macOS)

### 1. Xcode安装

```bash
# 从App Store安装Xcode
# 或下载Xcode命令行工具
xcode-select --install
```

### 2. iOS工具安装

```bash
# 安装ios-deploy
npm install -g ios-deploy

# 安装ideviceinstaller (可选)
brew install ideviceinstaller

# 安装xcpretty (可选,用于格式化输出)
gem install xcpretty
```

### 3. iOS模拟器验证

```bash
# 列出可用的模拟器
xcrun simctl list devices

# 启动模拟器
xcrun simctl boot "iPhone 14"
```

## 🚀 Appium安装

### 1. 全局安装Appium

```bash
# 安装最新版本的Appium
npm install -g appium

# 验证安装
appium --version
```

### 2. 安装Appium驱动

```bash
# Android驱动
appium driver install uiautomator2

# iOS驱动 (仅macOS)
appium driver install xcuitest

# 验证驱动安装
appium driver list --installed
```

### 3. 安装Appium Doctor

```bash
# 安装诊断工具
npm install -g appium-doctor

# 检查Android环境
appium-doctor --android

# 检查iOS环境 (仅macOS)
appium-doctor --ios
```

## 📦 Appium MCP Server安装

### 1. 从PyPI安装 (推荐)

```bash
# 安装最新版本
pip install appium-mcp-server

# 或指定版本
pip install appium-mcp-server==1.0.0
```

### 2. 从源码安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/appium-mcp.git
cd appium-mcp

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate     # Windows

# 安装依赖
pip install -e .
```

### 3. 使用Poetry安装 (开发者)

```bash
# 安装Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 安装项目依赖
poetry install

# 激活虚拟环境
poetry shell
```

## ✅ 安装验证

### 1. 检查MCP Server

```bash
# 检查安装
appium-mcp-server --version

# 显示帮助信息
appium-mcp-server --help
```

### 2. 运行健康检查

```bash
# 运行系统检查
appium-mcp-server doctor

# 检查设备连接
appium-mcp-server devices
```

### 3. 启动测试服务器

```bash
# 启动服务器 (stdio模式)
appium-mcp-server

# 启动服务器 (HTTP模式)
appium-mcp-server --transport http --port 8080
```

## 🔧 配置文件

### 1. 创建配置文件

```bash
# 生成默认配置
appium-mcp-server init-config

# 配置文件位置
# Linux/macOS: ~/.config/appium-mcp/config.yaml
# Windows: %APPDATA%\appium-mcp\config.yaml
```

### 2. 配置示例

```yaml
# ~/.config/appium-mcp/config.yaml
server:
  host: "localhost"
  port: 4723
  timeout: 30

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
```

## 🐛 常见问题解决

### 1. Python版本问题

```bash
# 错误: Python版本过低
# 解决: 升级Python或使用pyenv管理多版本

# 安装pyenv (macOS)
brew install pyenv

# 安装Python 3.11
pyenv install 3.11.0
pyenv global 3.11.0
```

### 2. Android SDK路径问题

```bash
# 错误: ANDROID_HOME未设置
# 解决: 正确设置环境变量

# 查找SDK路径
find / -name "platform-tools" 2>/dev/null

# 设置环境变量
export ANDROID_HOME=/path/to/android/sdk
```

### 3. iOS权限问题

```bash
# 错误: 无法访问iOS模拟器
# 解决: 授权Xcode命令行工具

sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -license accept
```

### 4. 端口占用问题

```bash
# 错误: 端口4723已被占用
# 解决: 查找并终止占用进程

# 查找占用进程
lsof -i :4723  # macOS/Linux
netstat -ano | findstr :4723  # Windows

# 终止进程
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

## 🔄 更新和卸载

### 1. 更新到最新版本

```bash
# PyPI安装的更新
pip install --upgrade appium-mcp-server

# 源码安装的更新
cd appium-mcp
git pull origin main
pip install -e .
```

### 2. 完全卸载

```bash
# 卸载Python包
pip uninstall appium-mcp-server

# 删除配置文件
rm -rf ~/.config/appium-mcp  # Linux/macOS
rmdir /s "%APPDATA%\appium-mcp"  # Windows

# 卸载Appium (可选)
npm uninstall -g appium
```

## 📞 获取帮助

如果在安装过程中遇到问题:

1. 查看 [故障排除文档](troubleshooting.md)
2. 运行 `appium-mcp-server doctor` 进行诊断
3. 查看 [GitHub Issues](https://github.com/your-repo/appium-mcp/issues)
4. 提交新的Issue并附上错误日志

---

> 💡 **提示**: 建议在安装完成后运行一次完整的健康检查，确保所有组件都正常工作。 