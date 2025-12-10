
import os
import sys
from utils import load_env
import json


def require_env(keys):
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        print("缺少环境变量: " + ", ".join(missing))
        print("请创建 .env 或在终端导出变量，参考 .env.example")
        sys.exit(1)


def run():
    from graph import app

    stream = True
    graph = False

    course_title = "2.1 探秘生成式人工智能"
    course_desc = "生成式人工智能的应用，生成式人工智能的发展历程，主流模型的区别"

    inputs = {
        "course_title": course_title,
        "course_desc": course_desc,
        "user_request": "",
        "knowledge": "这里是知识库内容...",
        "expect_gen_task_num": 4,
    }
    if stream:
        print('stream模式')
        output_path = os.path.join(os.getcwd(), "stream_output.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            for event in app.stream(inputs, stream_mode="updates", config={"recursion_limit": 60}):
                s = json.dumps(event, ensure_ascii=False, indent=2)
                f.write(s + "\n")
                print('--------')
    elif graph:
        print(app.get_graph().print_ascii())
    else:
        final = app.invoke(inputs)
        outline = final.get("outline", [])
        tasks = final.get("tasks", [])
        print("最终大纲:", outline)
        print("任务数量:", len(tasks))


def main():
    load_env(os.path.join(os.getcwd(), ".env"))
    require_env(["LLM_MODEL", "LLM_BASE_URL", "LLM_API_KEY"])
    run()


if __name__ == "__main__":
    main()
