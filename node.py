from langgraph.prebuilt import ToolNode
from state import AgentState
from llm import llm, llm_with_tools
from tool import tools
from langchain_core.messages import SystemMessage, HumanMessage
import json

# --- 节点 1: Agent (思考与决策) ---


def planner_node(state: AgentState):
    messages = state['messages']
    last = messages[-1] if messages else None
    text = getattr(last, "content", str(last)) if last else ""
    sys = "你是一个规划助手。仅返回 JSON 对象，键为 steps，值为不超过 9 条的字符串数组。不要输出除 JSON 外的任何内容。"
    user = "根据目标生成可执行计划。目标：" + text
    response = llm.invoke(
        [SystemMessage(content=sys), HumanMessage(content=user)])
    content = getattr(response, "content", "")
    steps = []
    try:
        data = json.loads(content)
        steps = [str(s) for s in data.get("steps", [])]
    except Exception:
        steps = [s for s in content.splitlines() if s]
    return {"planner_messages": [response], "goal": text, "plan": steps, "step_index": 0, "step_outputs": []}


def agent_node(state: AgentState):
    # messages = state['messages']
    plan = state.get("plan", [])
    idx = state.get("step_index", 0)
    prev = state.get("step_outputs", [])
    goal = state.get("goal", "")
    step = plan[idx] if idx < len(plan) else ""
    sys = "你是一个执行代理。针对给定的单一步骤进行执行，必要时使用可用工具。仅完成当前步骤并返回简洁可用的结果。"
    user = "当前步骤：" + step + "\n已完成结果：" + "; ".join(prev) + "\n用户目标：" + goal
    response = llm_with_tools.invoke(
        [SystemMessage(content=sys), HumanMessage(content=user)])
    return {"messages": [response]}


# --- 节点 2: Tools (执行) ---
# LangGraph 自带了一个 ToolNode，它会自动解析 LLM 的 tool_calls 并运行对应函数
tool_node = ToolNode(tools)


def post_exec_node(state: AgentState):
    messages = state['messages']
    last = messages[-1]
    content = getattr(last, "content", str(last))
    outputs = state.get("step_outputs", [])
    idx = state.get("step_index", 0)
    return {"step_outputs": outputs + [content], "step_index": idx + 1}
