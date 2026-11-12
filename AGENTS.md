# Skydoor 开发规范

## 项目定位与结构

Skydoor 是处于初步开发阶段的 Python Agent 框架，要求 Python >= 3.11。目前支持异步文本对话、会话历史、三种 LLM API 适配及部分异常重试；工具调用和自主多步执行尚未实现。以实际代码为准，不将规划中的能力当作现有功能。

- `src/skydoor/core/`：Agent 编排、消息、会话及统一请求/响应模型。
- `src/skydoor/llm/provider.py`：`LLMProvider` 协议。
- `src/skydoor/llm/providers/`：各 API 的参数映射、调用和响应转换，以及本地 Mock。
- `src/skydoor/errors/`：框架异常与可重试标记。
- `src/skydoor/utils/`：通用辅助逻辑，仅在确有复用需求时添加。
- `examples/`：可运行的使用示例。
- `tests/`：自动化测试。

## 环境与常用命令

统一使用 **uv** 管理 Python 环境、依赖和命令执行。遵循 `.python-version`，不要使用全局 Python、直接调用 `.venv` 中的解释器或用 pip 绕过 uv 管理依赖。以下命令在项目根目录执行：

```powershell
uv sync                              # 同步环境及默认开发依赖
uv run .\examples\basic_chat.py       # 运行示例（会调用真实模型）
uv run pytest                        # 运行测试
uv run pytest tests/test_example.py   # 运行指定测试，替换为实际路径
uv run ruff check .                  # 静态检查
uv run ruff format --check .          # 格式检查
uv run ruff format <修改的文件路径>   # 仅格式化相关文件
uv add <包名>                        # 添加运行依赖
uv add --dev <包名>                   # 添加开发依赖
uv remove <包名>                      # 移除依赖
```

依赖变更应同步维护 `pyproject.toml` 和 `uv.lock`；不要手工修改锁文件或顺带升级无关依赖。环境问题应先检查 uv 和项目配置，不以切换全局解释器掩盖问题。

## 设计与编码约定

- 保持实现简单、改动聚焦；优先沿用现有结构，不提前引入复杂抽象或无关依赖。
- 遵循 PEP 8 和项目 Ruff 配置。函数、变量使用 `snake_case`，类使用 `PascalCase`，常量使用 `UPPER_SNAKE_CASE`；新增或修改的公共接口补全准确的类型标注。
- LLM I/O 使用 `async` / `await`；异步路径不得使用阻塞式网络调用或 `time.sleep()`。
- `Agent` 负责流程编排，Provider 负责协议差异；避免让 SDK 类型和厂商字段泄漏到核心层。
- 新 Provider 遵循 `LLMProvider.complete(request) -> LLMResponse`。共享逻辑确有重复时再提取，保留各 API 的必填字段和能力差异。
- 明确默认值、`None` 和单次覆盖的语义。当前 `run()` 的 `None` 表示沿用 Agent 配置；请求层的 `None` 通常表示省略参数，Provider 的必填参数需单独处理。
- 修改消息结构、构造参数或返回值前检查调用方；接口变化应同步更新示例和文档。
- 注释和文档优先使用中文，重点解释设计原因、边界条件及约束，避免重复描述代码。

## 异常、状态与资源

- Provider 的 SDK 异常应转换为框架 `LLMError`，用 `raise ... from e` 保留原因，并明确 `retryable`。当前仅 Chat Completion 已实现完整转换，扩展其他 Provider 时需补齐。
- 仅对瞬时故障重试；认证、参数或配额耗尽等错误不应盲目重试。评估 SDK 内置重试与 Agent 重试叠加后的次数和延迟。
- 保持会话一致性：成功后才记录助手回复，失败时回滚本轮修改。修改执行流程时考虑取消任务和并发访问；当前同一 Agent 不应假定支持并发 `run()`。
- 不吞掉异常，不将失败伪装为成功的空回复；按场景处理空响应、截断和非成功状态。
- 框架日志使用 `logging`，示例可以使用 `print`。新增客户端或资源管理逻辑时明确生命周期及关闭方式。

## 测试与验证

- 行为变更和缺陷修复应补充有意义的测试，重点覆盖历史组装、参数映射、响应解析、重试边界和失败回滚；纯文档或格式修改无需新增测试。
- 使用 pytest；异步测试使用 pytest-asyncio。优先 Mock Provider 或 SDK 客户端，默认测试不得依赖网络、真实密钥或付费模型调用。
- 重试测试替换等待逻辑或使用零退避，避免实际等待。断言对外行为和关键边界，不机械复刻实现。
- 先运行受影响测试，再执行必要的回归及 Ruff 检查。发现历史问题时区分已有问题与本次引入的问题，避免无关批量修复。
- `tests/` 当前为空；pytest 未收集到测试不代表测试通过。真实示例仅在需要联调且已具备授权和配置时运行。
- 完成后说明修改内容、实际执行的检查和结果；未运行或被环境阻塞的检查应如实说明。

## 配置、文档与协作

- 密钥、服务地址和模型配置通过环境变量提供；示例可使用 `python-dotenv` 加载本地 `.env`。不要在源码、测试、日志或提交中暴露密钥及敏感对话。
- 示例当前使用 `AGNES_BASE_URL`、`AGNES_API_KEY`、`AGNES_MODEL`；说明配置时仅使用变量名或占位值，不读取或展示真实密钥。
- 开始修改前查看相关代码与工作区状态，保留用户已有改动；不擅自覆盖、回退或清理无关文件。
- 功能和用法变化同步维护 README 与示例；版本发布时保持包版本和变更记录一致，不为普通修改自动提升版本。
- 提交信息沿用 `feat:`、`fix:` 等前缀，简要说明目的。仅在用户要求时提交、推送或发布。
