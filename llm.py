from langchain_openai import ChatOpenAI
import os
from tool import tools

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")

llm = ChatOpenAI(model=LLM_MODEL, temperature=0, api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

llm_with_tools = llm.bind_tools(tools)