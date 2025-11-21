from langchain_core.tools import tool


@tool
def magic_search(query: str):
    """当需要查询实时信息或不懂的问题时使用此工具。"""
    # 这里通常对接 Google Search API 或 Tavily
    return f"搜索结果: 关于 {query} 的最新消息是......(这是模拟数据)"


tools = [magic_search]
