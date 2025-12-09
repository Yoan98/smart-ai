from state import AgentState
from llm import llm
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from typing import List
from prompts import PLANNER_SYSTEM_PROMPT, EXECUTOR_SYSTEM_PROMPT
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
    course_title = state.get("course_title", "")
    course_desc = state.get("course_desc", "")
    user_request = state.get("user_request", "")
    knowledge = state.get("knowledge", "")
    sys = PLANNER_SYSTEM_PROMPT
    user = f"""
    课程标题：{course_title}
    课程描述：{course_desc}
    用户需求：{user_request or "无"}
    知识库：{knowledge}
    
    请根据以上信息规划教学大纲。
    """
    structured = llm.with_structured_output(PlannerOut)
    result = structured.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
    items = getattr(result, "outline", [])
    outline = [{"title": str(i.title), "requirement": str(i.requirement)} for i in items]
    return {"outline": outline, "current_index": 0, "tasks": []}


def executor_node(state: AgentState):
    outline = state.get("outline", [])
    idx = state.get("current_index", 0)
    course_title = state.get("course_title", "")
    course_desc = state.get("course_desc", "")

    if idx >= len(outline):
        return {}
    current = outline[idx]
    sys = EXECUTOR_SYSTEM_PROMPT
    user = f"""
    课程标题：{course_title}
    课程描述：{course_desc}

    当前任务标题：{current.get("title", "")}
    当前任务详细要求：
    {current.get("requirement", "")}

    请生成一条符合系统约束的教学任务条目，并仅以严格 JSON 对象输出。
    """
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
