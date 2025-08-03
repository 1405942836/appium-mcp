"""
提示模板管理器。

管理和提供预定义的提示模板，帮助AI助手更好地使用Appium MCP工具。
"""

from typing import Any, Dict, List

from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent, Role

import structlog

logger = structlog.get_logger(__name__)


class PromptManager:
    """提示模板管理器。"""

    def __init__(self) -> None:
        """初始化提示模板管理器。"""
        self._prompts: Dict[str, Prompt] = {}
        self._initialize_prompts()

    def _initialize_prompts(self) -> None:
        """初始化预定义的提示模板。"""
        
        # 设备连接提示
        self._prompts["connect_device"] = Prompt(
            name="connect_device",
            description="连接移动设备的完整流程指导",
            arguments=[
                PromptArgument(
                    name="platform",
                    description="目标平台 (android/ios)",
                    required=False,
                ),
                PromptArgument(
                    name="app_info",
                    description="应用信息 (包名或Bundle ID)",
                    required=False,
                ),
            ],
        )

        # UI自动化测试提示
        self._prompts["ui_automation"] = Prompt(
            name="ui_automation",
            description="UI自动化测试的最佳实践指导",
            arguments=[
                PromptArgument(
                    name="test_scenario",
                    description="测试场景描述",
                    required=True,
                ),
                PromptArgument(
                    name="platform",
                    description="目标平台 (android/ios)",
                    required=False,
                ),
            ],
        )

        # 应用测试提示
        self._prompts["app_testing"] = Prompt(
            name="app_testing",
            description="移动应用测试的完整流程指导",
            arguments=[
                PromptArgument(
                    name="app_type",
                    description="应用类型 (native/hybrid/web)",
                    required=False,
                ),
                PromptArgument(
                    name="test_objectives",
                    description="测试目标和重点",
                    required=True,
                ),
            ],
        )

        # 问题诊断提示
        self._prompts["troubleshooting"] = Prompt(
            name="troubleshooting",
            description="移动设备和应用问题诊断指导",
            arguments=[
                PromptArgument(
                    name="issue_description",
                    description="问题描述",
                    required=True,
                ),
                PromptArgument(
                    name="platform",
                    description="平台信息",
                    required=False,
                ),
            ],
        )

        # 性能测试提示
        self._prompts["performance_testing"] = Prompt(
            name="performance_testing",
            description="移动应用性能测试指导",
            arguments=[
                PromptArgument(
                    name="performance_metrics",
                    description="关注的性能指标",
                    required=False,
                ),
            ],
        )

    def list_prompts(self) -> List[Prompt]:
        """
        获取所有可用的提示模板。

        Returns:
            提示模板列表
        """
        return list(self._prompts.values())

    def get_prompt(self, name: str, arguments: Dict[str, Any]) -> List[PromptMessage]:
        """
        获取指定的提示模板内容。

        Args:
            name: 提示模板名称
            arguments: 提示参数

        Returns:
            提示消息列表
        """
        if name not in self._prompts:
            raise ValueError(f"Prompt not found: {name}")

        logger.info("Generating prompt", name=name, arguments=arguments)

        if name == "connect_device":
            return self._generate_connect_device_prompt(arguments)
        elif name == "ui_automation":
            return self._generate_ui_automation_prompt(arguments)
        elif name == "app_testing":
            return self._generate_app_testing_prompt(arguments)
        elif name == "troubleshooting":
            return self._generate_troubleshooting_prompt(arguments)
        elif name == "performance_testing":
            return self._generate_performance_testing_prompt(arguments)
        else:
            raise ValueError(f"Prompt generator not implemented: {name}")

    def _generate_connect_device_prompt(self, arguments: Dict[str, Any]) -> List[PromptMessage]:
        """生成设备连接提示。"""
        platform = arguments.get("platform", "")
        app_info = arguments.get("app_info", "")

        platform_specific = ""
        if platform.lower() == "android":
            platform_specific = """
对于Android设备：
- 确保启用了开发者选项和USB调试
- 检查ADB连接状态
- 如果是模拟器，确保模拟器已启动
- 应用包名格式：com.example.app
- 可以指定启动Activity：com.example.app.MainActivity
"""
        elif platform.lower() == "ios":
            platform_specific = """
对于iOS设备：
- 真机需要开发者证书和配置文件
- 模拟器需要Xcode和iOS SDK
- 应用Bundle ID格式：com.example.app
- 确保WebDriverAgent已正确配置
"""

        app_specific = ""
        if app_info:
            app_specific = f"""
目标应用信息：{app_info}
"""

        content = f"""# 移动设备连接指导

你是一个专业的移动设备自动化测试助手。请帮助用户连接移动设备并开始自动化测试。

## 连接步骤

1. **发现设备**
   - 使用 `list_devices` 工具查看所有可用设备
   - 检查设备状态和平台信息

2. **连接设备**
   - 使用 `connect_device` 工具连接到指定设备
   - 根据需要配置应用启动参数

3. **验证连接**
   - 使用 `get_session_info` 检查会话状态
   - 可以截图验证设备连接正常

{platform_specific}

{app_specific}

## 最佳实践

- 连接前确保设备处于解锁状态
- 对于应用测试，建议先安装目标应用
- 保持设备电量充足，避免测试中断
- 使用稳定的USB连接，避免网络连接问题

## 故障排除

如果连接失败：
1. 检查设备是否在设备列表中
2. 验证设备驱动是否正确安装
3. 确认Appium服务器正在运行
4. 检查端口是否被占用

请告诉我你想要连接的设备类型和测试目标，我将为你提供具体的连接步骤。
"""

        return [
            PromptMessage(
                role=Role.user,
                content=TextContent(
                    type="text",
                    text=content,
                ),
            )
        ]

    def _generate_ui_automation_prompt(self, arguments: Dict[str, Any]) -> List[PromptMessage]:
        """生成UI自动化提示。"""
        test_scenario = arguments.get("test_scenario", "")
        platform = arguments.get("platform", "")

        platform_tips = ""
        if platform.lower() == "android":
            platform_tips = """
## Android UI自动化技巧

- 优先使用resource-id定位元素
- 使用UiAutomator表达式进行复杂查找
- 注意Android版本差异对UI的影响
- 利用content-desc进行无障碍定位
"""
        elif platform.lower() == "ios":
            platform_tips = """
## iOS UI自动化技巧

- 使用accessibility id进行元素定位
- 利用iOS Predicate进行复杂查找
- 注意iOS版本和设备尺寸差异
- 使用Class Chain进行层级定位
"""

        content = f"""# UI自动化测试指导

你是一个专业的移动UI自动化测试专家。请帮助用户实现高效、稳定的UI自动化测试。

## 测试场景
{test_scenario}

## UI自动化最佳实践

### 1. 元素定位策略
- **稳定性优先**：选择不易变化的属性
- **唯一性保证**：确保定位器能唯一标识元素
- **性能考虑**：避免复杂的XPath表达式

### 2. 元素定位优先级
1. ID (resource-id / accessibility id)
2. Name / Content Description
3. Class Name + 其他属性
4. XPath (最后选择)

### 3. 等待策略
- 使用显式等待而非固定延时
- 等待元素可见和可交互
- 设置合理的超时时间

### 4. 操作流程
1. **查找元素** - 使用 `find_element` 确认元素存在
2. **验证状态** - 检查元素是否可交互
3. **执行操作** - 点击、输入、滑动等
4. **验证结果** - 截图或检查状态变化

{platform_tips}

## 常用工具组合

### 基础操作流程
```
1. find_element → 查找目标元素
2. click_element → 点击元素
3. take_screenshot → 截图验证
```

### 表单填写流程
```
1. find_element → 查找输入框
2. input_text → 输入文本
3. find_element → 查找提交按钮
4. click_element → 提交表单
```

### 列表操作流程
```
1. find_element → 查找列表容器
2. swipe → 滑动查找目标项
3. click_element → 点击目标项
```

## 调试技巧

- 经常截图记录测试过程
- 使用元素高亮功能
- 记录详细的测试日志
- 分步验证每个操作

请描述你的具体测试需求，我将为你提供详细的实现方案。
"""

        return [
            PromptMessage(
                role=Role.user,
                content=TextContent(
                    type="text",
                    text=content,
                ),
            )
        ]

    def _generate_app_testing_prompt(self, arguments: Dict[str, Any]) -> List[PromptMessage]:
        """生成应用测试提示。"""
        app_type = arguments.get("app_type", "native")
        test_objectives = arguments.get("test_objectives", "")

        content = f"""# 移动应用测试指导

你是一个专业的移动应用测试专家。请帮助用户制定和执行完整的应用测试方案。

## 应用类型
{app_type.title()} 应用

## 测试目标
{test_objectives}

## 测试方案

### 1. 功能测试
- **核心功能验证**：确保主要功能正常工作
- **边界条件测试**：测试输入边界和异常情况
- **用户流程测试**：验证完整的用户使用路径

### 2. UI/UX测试
- **界面布局**：检查元素位置和对齐
- **响应式设计**：测试不同屏幕尺寸适配
- **交互反馈**：验证按钮点击、动画效果

### 3. 兼容性测试
- **设备兼容性**：测试不同设备和屏幕尺寸
- **系统版本**：验证不同OS版本的兼容性
- **性能表现**：监控应用在不同设备上的性能

## 测试执行流程

### 阶段一：环境准备
1. 使用 `list_devices` 查看可用设备
2. 使用 `connect_device` 连接目标设备
3. 确保应用已安装或准备安装包

### 阶段二：基础功能测试
1. 应用启动和初始化
2. 主要功能模块测试
3. 数据输入和验证

### 阶段三：用户体验测试
1. 导航流程测试
2. 错误处理测试
3. 性能和响应速度测试

### 阶段四：回归测试
1. 核心功能回归
2. 修复验证
3. 整体流程验证

## 测试工具使用建议

### 基础工具
- `find_element` - 元素定位和验证
- `click_element` - 用户交互模拟
- `input_text` - 文本输入测试
- `take_screenshot` - 结果记录和验证

### 高级工具
- `swipe` - 手势操作和滑动
- `get_device_info` - 设备信息收集
- `get_session_info` - 测试状态监控

## 测试报告

建议记录以下信息：
- 测试设备和环境信息
- 执行的测试用例和结果
- 发现的问题和截图证据
- 性能数据和观察结果

请告诉我你想要测试的具体功能或场景，我将为你提供详细的测试方案。
"""

        return [
            PromptMessage(
                role=Role.user,
                content=TextContent(
                    type="text",
                    text=content,
                ),
            )
        ]

    def _generate_troubleshooting_prompt(self, arguments: Dict[str, Any]) -> List[PromptMessage]:
        """生成问题诊断提示。"""
        issue_description = arguments.get("issue_description", "")
        platform = arguments.get("platform", "")

        content = f"""# 移动设备问题诊断指导

你是一个专业的移动设备问题诊断专家。请帮助用户分析和解决移动设备自动化测试中的问题。

## 问题描述
{issue_description}

## 诊断流程

### 1. 信息收集
- 使用 `list_devices` 检查设备连接状态
- 使用 `get_device_info` 获取详细设备信息
- 使用 `list_sessions` 查看当前会话状态
- 使用 `take_screenshot` 获取当前屏幕状态

### 2. 常见问题分类

#### 连接问题
- 设备未被识别
- 连接超时或失败
- 会话意外断开

#### 元素定位问题
- 元素找不到
- 元素定位不稳定
- 元素状态异常

#### 操作执行问题
- 点击无响应
- 输入失败
- 手势操作异常

#### 性能问题
- 操作响应慢
- 应用崩溃
- 内存不足

### 3. 诊断步骤

#### 第一步：基础检查
1. 确认设备连接状态
2. 检查Appium服务器状态
3. 验证应用是否正常运行

#### 第二步：定位问题
1. 重现问题场景
2. 收集错误日志
3. 分析失败原因

#### 第三步：解决方案
1. 应用对应的解决方法
2. 验证修复效果
3. 记录解决过程

## 常见问题解决方案

### 设备连接问题
- 检查USB调试是否开启
- 重启ADB服务
- 更新设备驱动
- 检查端口占用情况

### 元素定位问题
- 使用更稳定的定位策略
- 增加等待时间
- 检查元素属性变化
- 使用截图辅助调试

### 应用兼容性问题
- 检查系统版本兼容性
- 更新应用版本
- 调整自动化脚本
- 使用设备特定配置

## 预防措施

1. **环境稳定性**
   - 使用稳定的网络连接
   - 保持设备电量充足
   - 定期清理设备存储空间

2. **脚本健壮性**
   - 添加异常处理
   - 使用重试机制
   - 实现优雅降级

3. **监控和日志**
   - 启用详细日志记录
   - 监控系统资源使用
   - 定期备份测试数据

请提供更多关于问题的详细信息，我将为你提供针对性的诊断和解决方案。
"""

        return [
            PromptMessage(
                role=Role.user,
                content=TextContent(
                    type="text",
                    text=content,
                ),
            )
        ]

    def _generate_performance_testing_prompt(self, arguments: Dict[str, Any]) -> List[PromptMessage]:
        """生成性能测试提示。"""
        performance_metrics = arguments.get("performance_metrics", "")

        content = f"""# 移动应用性能测试指导

你是一个专业的移动应用性能测试专家。请帮助用户设计和执行全面的性能测试方案。

## 关注的性能指标
{performance_metrics or "启动时间、响应速度、内存使用、CPU占用、电池消耗"}

## 性能测试维度

### 1. 启动性能
- **冷启动时间**：应用首次启动的时间
- **热启动时间**：应用从后台恢复的时间
- **启动成功率**：不同条件下的启动成功率

### 2. 响应性能
- **操作响应时间**：用户操作到界面反馈的时间
- **页面加载时间**：页面切换和内容加载时间
- **网络请求延迟**：API调用和数据获取时间

### 3. 资源使用
- **内存占用**：应用运行时的内存使用情况
- **CPU利用率**：处理器占用率和热量产生
- **存储空间**：应用安装包大小和数据存储

### 4. 稳定性能
- **长时间运行**：连续使用的稳定性
- **内存泄漏**：长期运行的内存增长情况
- **崩溃率**：应用异常退出的频率

## 性能测试方法

### 基准测试
1. 建立性能基准线
2. 定义可接受的性能范围
3. 设置性能监控阈值

### 负载测试
1. 模拟正常使用负载
2. 测试峰值负载处理能力
3. 评估资源使用效率

### 压力测试
1. 超出正常负载的压力测试
2. 确定系统崩溃点
3. 验证错误处理机制

## 测试执行策略

### 测试环境准备
1. 使用代表性设备进行测试
2. 控制测试环境变量
3. 准备性能监控工具

### 测试数据收集
1. 使用自动化脚本收集数据
2. 记录关键性能指标
3. 保存测试过程截图和日志

### 结果分析
1. 对比不同版本的性能差异
2. 识别性能瓶颈和优化点
3. 生成性能测试报告

## 使用Appium MCP工具进行性能测试

### 基础监控
```
1. connect_device → 连接测试设备
2. take_screenshot → 记录测试过程
3. get_session_info → 监控会话状态
```

### 自动化测试流程
```
1. 启动应用并记录启动时间
2. 执行核心功能操作
3. 监控资源使用情况
4. 记录性能数据
```

### 长时间稳定性测试
```
1. 设计循环测试脚本
2. 定期收集性能数据
3. 监控异常和错误
4. 生成趋势分析报告
```

## 性能优化建议

### 应用层优化
- 优化启动流程和初始化逻辑
- 减少不必要的资源加载
- 实现高效的缓存策略
- 优化图片和媒体资源

### 系统层优化
- 合理使用系统资源
- 优化后台任务处理
- 减少电池消耗
- 提升用户体验流畅度

请告诉我你想要测试的具体性能方面，我将为你提供详细的测试方案和实施指导。
"""

        return [
            PromptMessage(
                role=Role.user,
                content=TextContent(
                    type="text",
                    text=content,
                ),
            )
        ] 