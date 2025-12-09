EXECUTOR_FIELD_DESCRIPTIONS = {
    "sort": "任务序号，从 1 开始，与执行顺序一致",
    "type": "题型类别：1=选择题，2=填空题，3=问答题。根据任务内容选择最匹配的类型",
    "title": "任务标题，简洁明确，能够概括任务核心目标",
    "content": "任务正文，使用 Markdown 编写。应包含：题干、操作或作答说明、必要材料或上下文、评价标准或提示",
    "answer_r": "标准答案或参考答案，格式清晰、可评估",
    "single_report_prompt": "针对该任务的评估与反馈提示语，用于生成单任务报告",
    "general_report_prompt": "用于整场教学的汇总报告提示语，可整合多任务表现",
}


def build_executor_system_prompt(field_desc: dict[str, str]) -> str:
    fields = ", ".join([
        f"{k}(string)" if k in {"title", "content", "answer_r", "single_report_prompt", "general_report_prompt"}
        else f"{k}(number)" for k in field_desc.keys()
    ])
    details = "\n".join([f"- {k}：{v}" for k, v in field_desc.items()])
    return (
        "你是教学任务生成助手。\n"
        + "仅输出严格 JSON 对象，不得包含代码块标记或额外文本。\n"
        + "必须包含字段：" + fields + "。\n"
        + details + "\n"
        + "类型约束：type 仅可为 1/2/3；sort 使用当前任务序号；content 必须为 Markdown，结构清晰；answer_r 与题型匹配。\n"
        + "输出格式：不换层级，不嵌套数组，仅返回单个任务对象。"
    )

