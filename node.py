from state import AgentState
from llm import llm
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from typing import List
from prompts import (
    PLANNER_SYSTEM_PROMPT,
    BASE_FIELD_GEN_PROMPT,
    SINGLE_REPORT_PROMPT_GEN_PROMPT,
    GENERAL_REPORT_PROMPT_GEN_PROMPT
)


class OutlineItem(BaseModel):
    title: str
    requirement: str


class PlannerOut(BaseModel):
    outline: List[OutlineItem]


class BaseFieldModel(BaseModel):
    sort: int
    type: int
    title: str
    content: str
    answer_r: str


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
    # 初始化当前任务草稿
    print('+++++++++++++++')
    print('total tasks:', len(state.get("tasks", [])))
    print('current index:', state.get("current_index", 0))
    print('+++++++++++++++')
    return {"current_task_draft": {}}


def base_field_gen_node(state: AgentState):
    outline = state.get("outline", [])
    idx = state.get("current_index", 0)
    course_title = state.get("course_title", "")
    course_desc = state.get("course_desc", "")

    if idx >= len(outline):
        return {}

    current = outline[idx]
    sys = BASE_FIELD_GEN_PROMPT
    user = f"""
    课程标题：{course_title}
    课程描述：{course_desc}

    当前任务标题：{current.get("title", "")}
    当前任务详细要求：
    {current.get("requirement", "")}

    请生成一条符合系统约束的教学任务条目，并仅以严格 JSON 对象输出。
    """
    structured = llm.with_structured_output(BaseFieldModel)
    result = structured.invoke([SystemMessage(content=sys), HumanMessage(content=user)])

    draft = state.get("current_task_draft", {})
    draft.update({
        "sort": int(getattr(result, "sort", idx + 1)),
        "type": int(getattr(result, "type", 1)),
        "title": str(getattr(result, "title", "")),
        "content": str(getattr(result, "content", "")),
        "answer_r": str(getattr(result, "answer_r", "")),
    })
    return {"current_task_draft": draft}


def single_report_prompt_gen_node(state: AgentState):
    outline = state.get("outline", [])
    idx = state.get("current_index", 0)
    course_title = state.get("course_title", "")
    course_desc = state.get("course_desc", "")

    if idx >= len(outline):
        return {}

    current = outline[idx]
    # 获取已经生成的基础字段，以提供更多上下文
    draft = state.get("current_task_draft", {})
    task_content = draft.get("content", "")
    task_answer_r = draft.get("answer_r", "")

    sys = SINGLE_REPORT_PROMPT_GEN_PROMPT
    user = f"""
    课程标题：{course_title}
    课程描述：{course_desc}

    当前任务标题：{current.get("title", "")}
    当前任务详细要求：{current.get("requirement", "")}
    
    任务内容：
    {task_content}

    答案评价标准：
    {task_answer_r}

    请根据以上信息，生成单份学生报告的 System Prompt。
    """
    # 这里不需要结构化输出，直接获取字符串即可，或者定义一个包含单一字符串字段的模型
    # 为了简单，假设 LLM 直接返回字符串。如果需要 strictly json，可以使用 structured output 包含一个 prompt 字段。
    # 但 prompt 中可能包含 json 结构，直接返回 string 可能更好。
    # 既然之前的 prompt 要求 "请只输出生成的 system prompt 内容"，我们就直接 invoke。

    response = llm.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
    prompt_content = response.content

    draft.update({"single_report_prompt": prompt_content})
    return {"current_task_draft": draft}


def general_report_prompt_gen_node(state: AgentState):
    outline = state.get("outline", [])
    idx = state.get("current_index", 0)
    course_title = state.get("course_title", "")
    course_desc = state.get("course_desc", "")

    if idx >= len(outline):
        return {}

    current = outline[idx]
    draft = state.get("current_task_draft", {})

    sys = GENERAL_REPORT_PROMPT_GEN_PROMPT
    user = f"""
    课程标题：{course_title}
    课程描述：{course_desc}

    当前任务标题：{current.get("title", "")}
    当前任务详细要求：{current.get("requirement", "")}

    请根据以上信息，生成班级汇总报告的 System Prompt。
    """

    response = llm.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
    prompt_content = response.content

    draft.update({"general_report_prompt": prompt_content})
    return {"current_task_draft": draft}


def field_summary_node(state: AgentState):
    draft = state.get("current_task_draft", {})
    tasks = state.get("tasks", [])
    idx = state.get("current_index", 0)

    # 确保 draft 包含所有必要字段
    item = {
        "sort": draft.get("sort", idx + 1),
        "type": draft.get("type", 1),
        "title": draft.get("title", ""),
        "content": draft.get("content", ""),
        "answer_r": draft.get("answer_r", ""),
        "single_report_prompt": draft.get("single_report_prompt", ""),
        "general_report_prompt": draft.get("general_report_prompt", ""),
    }

    return {"tasks": tasks + [item], "current_index": idx + 1, "current_task_draft": {}}
