
import os
import sys
from langchain_core.messages import HumanMessage

from utils import load_env


def require_env(keys):
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        print("缺少环境变量: " + ", ".join(missing))
        print("请创建 .env 或在终端导出变量，参考 .env.example")
        sys.exit(1)


def run(goal: str, stream: bool, graph: bool):
    from graph import app

    inputs = {"messages": [HumanMessage(content=goal)]}
    if stream:
        print('stream模式')
        for event in app.stream(inputs, stream_mode="updates"):
            print(event)
            print('--------')
    elif graph:
        print(app.get_graph().print_ascii())
    else:
        final = app.invoke(inputs)
        plan = final.get("plan", [])
        outs = final.get("step_outputs", [])
        print("最终计划:", plan)
        print("最终结果:", outs)


def main():
    load_env(os.path.join(os.getcwd(), ".env"))
    require_env(["LLM_MODEL", "LLM_BASE_URL", "LLM_API_KEY"])
    run("帮我规划一次两天的城市短途旅行", False, True)


if __name__ == "__main__":
    main()
