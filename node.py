from state import AgentState
from llm import llm
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from typing import List
from prompts import build_executor_system_prompt, EXECUTOR_FIELD_DESCRIPTIONS
from state import OutlineItem


class PlannerOut(BaseModel):
    outline: List[OutlineItem]


class TaskItemModel(BaseModel):
    sort: int
    type: int
    title: str
    content: str
    answer_r: str
    single_report_prompt: str
    general_report_prompt: str


def plan_node(state: AgentState):
    user_request = state.get("user_request", "")
    knowledge = state.get("knowledge", "")
    sys = "你是教学任务规划助手。仅返回严格 JSON 对象，键为 outline，值为对象数组。每个对象包含字段：title(string)、desc(string)、requirement(string)。不得返回除该对象外的任何文本或代码块。"
    user = "用户需求：" + user_request + "\n知识库：" + knowledge
    structured = llm.with_structured_output(PlannerOut)
    result = structured.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
    items = getattr(result, "outline", [])
    outline = [{"title": str(i.title), "requirement": str(i.requirement)} for i in items]
    return {"outline": outline, "current_index": 0, "tasks": []}


def executor_node(state: AgentState):
    outline = state.get("outline", [])
    idx = state.get("current_index", 0)
    if idx >= len(outline):
        return {}
    current = outline[idx]
    sys = build_executor_system_prompt(EXECUTOR_FIELD_DESCRIPTIONS)
    user = (
        "任务标题：" + str(current.get("title", "")) + "\n"
        + "任务详细要求：" + str(current.get("requirement", "")) + "\n"
        + "请生成一条符合系统约束的教学任务条目，并仅以严格 JSON 对象输出。"
    )
    structured = llm.with_structured_output(TaskItemModel)
    result = structured.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
    item = {
        "sort": int(getattr(result, "sort", idx + 1)),
        "type": int(getattr(result, "type", 1)),
        "title": str(getattr(result, "title", "")),
        "content": str(getattr(result, "content", "")),
        "answer_r": str(getattr(result, "answer_r", "")),
        "single_report_prompt": str(getattr(result, "single_report_prompt", "")),
        "general_report_prompt": str(getattr(result, "general_report_prompt", "")),
    }
    tasks = state.get("tasks", [])
    return {"tasks": tasks + [item], "current_index": idx + 1}
