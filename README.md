# Smart-AI: General Task Agent Framework (Python + LangGraph)

一个可扩展的通用任务型 AI Agent 架构，支持自主规划、工具选择与执行，并以插件化工具系统实现模块化扩展。以 LangGraph StateGraph + Node 组织流程，LLM 决策驱动。

## 特性
- Planner Agent：根据用户输入进行任务规划（输出计划 JSON）
- Tool Executor：动态调用多个工具（自动注册，插件化扩展）
- Final Aggregator：汇总所有中间结果，生成最终响应
- LangGraph StateGraph：多步骤、有条件的图流程；流程由 LLM 决策驱动
- LLM 可配置：OpenAI / DeepSeek / Moonshot（以及内置 MockLLM 用于本地测试）

## 技术栈
- Python 3.10+
- LangGraph（StateGraph + Node）
- 可选 LLM：OpenAI / DeepSeek / Moonshot（通过环境变量配置）
- 测试：pytest

## 项目结构
```
smart-ai/
├── README.md
├── requirements.txt
├── src/
│   ├── app.py                        # 构建与运行 LangGraph
│   ├── core/
│   │   ├── graph/
│   │   │   ├── state.py             # State 类型定义
│   │   │   ├── nodes/
│   │   │   │   ├── planner.py       # Planner Node
│   │   │   │   ├── executor.py      # Tool Executor Node
│   │   │   │   └── aggregator.py    # Final Aggregator Node
│   │   ├── tools/
│   │   │   ├── base.py              # BaseTool 接口
│   │   │   ├── registry.py          # 工具自动注册
│   │   │   ├── outline.py           # 示例工具：大纲生成
│   │   │   ├── mindmap.py           # 示例工具：思维导图
│   │   │   └── search.py            # 示例工具：知识查询（本地 KB）
│   │   ├── llm/
│   │   │   ├── base.py              # LLMAdapter 接口
│   │   │   ├── provider.py          # LLM 选择器
│   │   │   └── providers/
│   │   │       ├── openai_adapter.py
│   │   │       ├── deepseek_adapter.py
│   │   │       └── moonshot_adapter.py
│   └── data/
│       └── knowledge_base.json      # 本地知识库示例
└── tests/
    ├── test_planner.py              # Planner Node 能解析探究式学习意图
    └── test_graph_run.py            # Graph 端到端运行
```

## 配置
通过环境变量选择 LLM：
- `LLM_PROVIDER`：`openai` | `deepseek` | `moonshot` | `mock`（默认：`mock`）
- `OPENAI_API_KEY` / 其他厂商密钥：按需配置
- `OPENAI_MODEL`：默认 `gpt-4o-mini`

## 快速开始
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

或直接运行一个示例：
```
python src/app.py "为高中生设计一个关于牛顿第二定律的探究式学习任务"
```
（默认使用 MockLLM，本地可离线运行）

## 设计说明
- 工具系统采用插件化：所有工具置于 `core/tools/`，继承 `BaseTool`，由 `ToolRegistry` 自动发现与注册。
- Planner Node 输出标准化计划 JSON，包含 `objective` 与 `steps`（每步指明工具与入参）。
- Tool Executor 根据计划执行工具并收集 `tool_results`。
- Final Aggregator 将所有工具结果统一整合为最终输出（若可用则调用 LLM，总是有离线回退）。

## 测试目标
- 探究式学习任务生成：验证 Planner Node 能解析用户意图并生成合理任务计划。
- Graph 完整运行：验证从输入到最终响应的端到端流程能正常完成。