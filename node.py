from state import AgentState
from llm import llm
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import List


class PlannerOut(BaseModel):
    outline: List[str] = Field(description="")
    requirements: str = Field(description="")


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
    sys = "你是教学任务规划助手。根据用户需求和知识，先输出一个 JSON：{\"outline\": [字符串...], \"requirements\": 详细要求字符串}。严格 JSON，且仅输出该对象。"
    user = "用户需求：" + user_request + "\n知识库：" + knowledge
    structured = llm.with_structured_output(PlannerOut)
    result = structured.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
    outline = [str(s) for s in getattr(result, "outline", [])]
    requirements = str(getattr(result, "requirements", ""))
    return {"outline": outline, "requirement_desc": requirements, "current_index": 0, "tasks": []}


def executor_node(state: AgentState):
    outline = state.get("outline", [])
    idx = state.get("current_index", 0)
    if idx >= len(outline):
        return {}
    topic = outline[idx]
    requirements = state.get("requirement_desc", "")
    sys = "你是教学任务生成助手。只输出严格 JSON 对象，无额外文本或代码块。字段：sort(number)、type(number:1选择题/2填空题/3问答题)、title(string)、content(string,markdown)、answer_r(string)、single_report_prompt(string)、general_report_prompt(string)。"
    user = "索引：" + str(idx + 1) + "\n主题：" + topic + "\n详细要求：" + requirements + "\n请生成一个符合要求的任务。"
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
