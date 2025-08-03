# 贡献指南

感谢您考虑为 Appium MCP Server 项目做出贡献！我们欢迎各种形式的贡献，包括但不限于：

- 🐛 Bug 报告
- 💡 功能建议
- 📝 文档改进
- 🔧 代码贡献
- 🧪 测试用例

## 开始之前

在开始贡献之前，请确保您已经：

1. 阅读了项目的 [README.md](README.md)
2. 查看了现有的 [Issues](https://github.com/your-repo/appium-mcp/issues) 和 [Pull Requests](https://github.com/your-repo/appium-mcp/pulls)
3. 了解了项目的 [行为准则](#行为准则)

## 开发环境设置

### 1. Fork 和 Clone 项目

```bash
# Fork 项目到您的 GitHub 账户，然后 clone
git clone https://github.com/your-username/appium-mcp.git
cd appium-mcp

# 添加上游仓库
git remote add upstream https://github.com/your-repo/appium-mcp.git
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit hooks
pre-commit install
```

### 3. 验证安装

```bash
# 运行测试
pytest

# 检查代码格式
black --check src tests
isort --check-only src tests
flake8 src tests

# 类型检查
mypy src
```

## 贡献流程

### 1. 创建分支

```bash
# 确保您在最新的 main 分支上
git checkout main
git pull upstream main

# 创建新的功能分支
git checkout -b feature/your-feature-name
# 或 git checkout -b fix/your-bug-fix
```

### 2. 进行更改

- 遵循现有的代码风格和约定
- 为新功能添加测试
- 更新相关文档
- 确保所有测试通过

### 3. 提交更改

```bash
# 添加更改
git add .

# 提交（会自动运行 pre-commit hooks）
git commit -m "feat: add new feature description"

# 推送到您的 fork
git push origin feature/your-feature-name
```

### 4. 创建 Pull Request

1. 在 GitHub 上创建 Pull Request
2. 填写 PR 模板
3. 等待代码审查
4. 根据反馈进行修改

## 代码规范

### Python 代码风格

我们使用以下工具来保持代码质量：

- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码检查
- **mypy**: 类型检查

### 提交信息规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

类型包括：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行的变动）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat(device): add iOS device support
fix(ui): resolve element finding timeout issue
docs(readme): update installation instructions
```

## 测试指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_device_manager.py

# 运行带覆盖率的测试
pytest --cov=appium_mcp

# 运行特定标记的测试
pytest -m "not slow"  # 跳过慢测试
pytest -m integration  # 只运行集成测试
```

### 编写测试

- 为新功能编写单元测试
- 为复杂功能编写集成测试
- 测试文件命名：`test_*.py`
- 测试函数命名：`test_*`

## 文档贡献

### 文档结构

```
docs/
├── README.md           # 文档索引
├── quickstart.md       # 快速开始
├── installation.md     # 安装指南
├── configuration.md    # 配置指南
├── architecture.md     # 架构设计
├── tools/             # 工具文档
└── examples/          # 使用示例
```

### 文档规范

- 使用 Markdown 格式
- 包含代码示例
- 保持内容更新
- 提供中英文版本（如适用）

## 发布流程

项目维护者负责发布新版本：

1. 更新版本号（`pyproject.toml`）
2. 更新 CHANGELOG.md
3. 创建 Git 标签
4. 发布到 PyPI

## 行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们承诺：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不当行为

不可接受的行为包括：

- 使用性化的语言或图像
- 人身攻击或政治攻击
- 公开或私人骚扰
- 未经许可发布他人的私人信息
- 其他在专业环境中不当的行为

## 获取帮助

如果您需要帮助或有疑问：

- 📖 查看 [文档](docs/README.md)
- 🐛 搜索或创建 [Issue](https://github.com/your-repo/appium-mcp/issues)
- 💬 参与 [讨论](https://github.com/your-repo/appium-mcp/discussions)
- 📧 联系维护者

## 致谢

感谢所有为项目做出贡献的开发者！您的贡献让这个项目变得更好。

---

再次感谢您的贡献！🎉