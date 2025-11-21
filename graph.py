from langgraph.graph import StateGraph, START, END
from typing import Literal
from state import AgentState
from node import agent_node, tool_node

# 这个函数用来决定下一步去哪里


def should_continue(state: AgentState) -> Literal["tools", END]:
    messages = state['messages']
    last_message = messages[-1]

    # 如果 LLM 的回复里包含 tool_calls，说明它想调工具
    if last_message.tool_calls:
        return "tools"  # 路由到名为 'tools' 的节点

    # 否则，说明任务结束
    return END


# 初始化图
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

# 添加边
# 1.以此开始
workflow.add_edge(START, "agent")

# 2.agent 之后的条件跳转
workflow.add_conditional_edges(
    "agent",           # 来源节点
    should_continue,   # 判断函数
)

# 3.工具执行完，必须回到 agent 再次思考（形成循环！）
workflow.add_edge("tools", "agent")

# 编译图
app = workflow.compile()
