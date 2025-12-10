
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

    course_title = "解锁最短路径的秘密"
    course_desc = "教材内容设计遵循“生活情境—实践探究—思维提升—应用延伸”的逻辑主线：先以地图（3行3列网格）为具象载体，让学生；再引导学生转变思路，通过规划算法方法计算从起点到所有节点的最短用时，接着找出最短用时的路径；最后拓展导航、物流、电力网络等生活应用场景，实现“从具象问题到抽象算法，再回归生活应用”的知识建构。"

    inputs = {
        "course_title": course_title,
        "course_desc": course_desc,
        "user_request": "",
        "knowledge": "这里是知识库内容...",
    }
    if stream:
        print('stream模式')
        output_path = os.path.join(os.getcwd(), "stream_output.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            for event in app.stream(inputs, stream_mode="updates"):
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
