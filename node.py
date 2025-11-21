from langgraph.prebuilt import ToolNode
from state import AgentState
from llm import llm_with_tools
from tool import tools

# --- 节点 1: Agent (思考与决策) ---


def agent_node(state: AgentState):
    messages = state['messages']
    # 调用绑定了工具的 LLM
    response = llm_with_tools.invoke(messages)
    # 返回更新后的状态（追加一条 AI 的回复）
    return {"messages": [response]}


# --- 节点 2: Tools (执行) ---
# LangGraph 自带了一个 ToolNode，它会自动解析 LLM 的 tool_calls 并运行对应函数
tool_node = ToolNode(tools)
