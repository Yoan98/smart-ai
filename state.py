from typing import TypedDict, List


class TaskItem(TypedDict):
    sort: int
    type: int
    title: str
    content: str
    answer_r: str
    single_report_prompt: str
    general_report_prompt: str


class OutlineItem(TypedDict):
    title: str
    requirement: str


class AgentState(TypedDict):
    user_request: str
    knowledge: str
    outline: List[OutlineItem]
    current_index: int
    tasks: List[TaskItem]
