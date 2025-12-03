import os
import sys
import argparse
from IPython.display import Image, display
from graph import app
from langchain_core.messages import HumanMessage


def load_env(path: str):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if not os.getenv(k):
                os.environ[k] = v


def require_env(keys):
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        print("缺少环境变量: " + ", ".join(missing))
        print("请创建 .env 或在终端导出变量，参考 .env.example")
        sys.exit(1)


def run(goal: str, stream: bool):
    inputs = {"messages": [HumanMessage(content=goal)]}
    if stream:
        print('stream模式')
        for event in app.stream(inputs, stream_mode="updates"):
             print(event)
             print('--------')
    else:
        final = app.invoke(inputs)
        plan = final.get("plan", [])
        outs = final.get("step_outputs", [])
        print("最终计划:", plan)
        print("最终结果:", outs)


def main():
    load_env(os.path.join(os.getcwd(), ".env"))
    require_env(["LLM_MODEL", "LLM_BASE_URL", "LLM_API_KEY"])
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", type=str, default="帮我规划一次两天的城市短途旅行")
    parser.add_argument("--stream", action="store_true",default=True)
    args = parser.parse_args()
    run(args.goal, args.stream)


if __name__ == "__main__":
    main()
