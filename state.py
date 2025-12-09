from typing import TypedDict, List


class TaskItem(TypedDict):
    sort: int
    type: int
    title: str
    content: str
    answer_r: str
    single_report_prompt: str
    general_report_prompt: str


class AgentState(TypedDict):
    user_request: str
    knowledge: str
    outline: List[str]
    current_index: int
    requirement_desc: str
    tasks: List[TaskItem]
