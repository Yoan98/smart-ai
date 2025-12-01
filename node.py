from langgraph.prebuilt import ToolNode
from state import AgentState
from llm import llm, llm_with_tools
from tool import tools
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from typing import List
import json

# --- 节点 1: Agent (思考与决策) ---


class IntentOut(BaseModel):
    objective: str = Field(description="用户目标的明确表达")
    demands: List[str] = Field(description="潜在诉求列表")
    constraints: List[str] = Field(description="约束条件列表")
    preferences: List[str] = Field(description="偏好或倾向列表")
    assumptions: List[str] = Field(description="为直接输出而作出的合理假设")


class PlanOut(BaseModel):
    steps: List[str] = Field(description="步骤数组")


def intent_node(state: AgentState):
    messages = state['messages']
    last = messages[-1] if messages else None
    text = getattr(last, "content", str(last)) if last else ""
    sys = (
        "你是一个意图分析助手。根据用户目标进行诉求拆解、约束识别与偏好提取。"
        "不得向用户提问。仅返回 JSON，对象需包含字段 objective, demands, constraints, preferences, assumptions。"
        "所有字段使用中文，列表项不超过 5 条，内容简洁可执行。"
    )
    user = "分析目标：" + text
    structured = llm.with_structured_output(IntentOut)
    result = structured.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
    objective = str(getattr(result, "objective", ""))
    demands = [str(s) for s in getattr(result, "demands", [])]
    constraints = [str(s) for s in getattr(result, "constraints", [])]
    preferences = [str(s) for s in getattr(result, "preferences", [])]
    assumptions = [str(s) for s in getattr(result, "assumptions", [])]
    intent = {
        "objective": objective,
        "demands": demands,
        "constraints": constraints,
        "preferences": preferences,
        "assumptions": assumptions,
    }
    goal = objective or text
    return {"goal": goal, "intent": intent}


def planner_node(state: AgentState):
    messages = state['messages']
    last = messages[-1] if messages else None
    text = getattr(last, "content", str(last)) if last else ""
    goal = state.get("goal", text)
    intent = state.get("intent", {})
    sys = (
        "你是一个规划助手。严格仅返回 JSON 对象，键为 steps，值为不超过 3 条的字符串数组。"
        "基于用户目标与诉求分析（包含约束、偏好、假设）生成最小可执行计划。"
        "不得向用户提问，不要输出除 JSON 外的任何内容。"
    )
    user = (
        "生成计划所需信息如下：\n"
        + "用户目标：" + goal + "\n"
        + "诉求分析：" + json.dumps(intent, ensure_ascii=False)
    )
    structured = llm.with_structured_output(PlanOut)
    result = structured.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
    steps = [str(s) for s in getattr(result, "steps", [])]
    ai_content = json.dumps({"steps": steps}, ensure_ascii=False)
    return { "goal": text, "plan": steps, "step_index": 0, "step_outputs": []}


def agent_node(state: AgentState):
    # messages = state['messages']
    plan = state.get("plan", [])
    idx = state.get("step_index", 0)
    prev = state.get("step_outputs", [])
    goal = state.get("goal", "")
    step = plan[idx] if idx < len(plan) else ""
    sys = "你是一个执行代理。针对给定的单一步骤直接产出可用结果，必要时使用可用工具。不得向用户提问；信息不足时进行合理假设并继续执行。仅返回简洁可用的结果。"
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
