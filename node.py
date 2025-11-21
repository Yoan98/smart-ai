from langgraph.prebuilt import ToolNode
from state import AgentState
from llm import llm, llm_with_tools
from tool import tools

# --- 节点 1: Agent (思考与决策) ---


def planner_node(state: AgentState):
    messages = state['messages']
    last = messages[-1]
    text = getattr(last, "content", str(last))
    prompt = "请根据目标生成可执行计划，每行一个步骤,不要超过9个步骤。\n目标：" + text
    response = llm.invoke(prompt)
    plan_text = getattr(response, "content", "")
    steps = [s.strip(" 0123456789.-) ")
             for s in plan_text.splitlines() if s.strip()]
    return {"messages": [response], "plan": steps, "step_index": 0, "step_outputs": []}


def agent_node(state: AgentState):
    messages = state['messages']
    plan = state.get("plan", [])
    idx = state.get("step_index", 0)
    prev = state.get("step_outputs", [])
    goal = getattr(messages[0], "content", str(
        messages[0])) if messages else ""
    step = plan[idx] if idx < len(plan) else ""
    prompt = "现在执行该步骤：" + step + "\n已完成结果：" + \
        "; ".join(prev) + "\n用户目标：" + goal + "\n需要时调用工具完成。"
    response = llm_with_tools.invoke(prompt)
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
