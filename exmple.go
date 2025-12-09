package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/cloudwego/eino-ext/components/model/openai"
	"github.com/cloudwego/eino/components/model"
	"github.com/cloudwego/eino/components/prompt"
	"github.com/cloudwego/eino/compose"
	"github.com/cloudwego/eino/schema"
)

// ================= 1. 定义 State (状态) =================

type TaskItem struct {
	Sort                int    `json:"sort"`
	Type                int    `json:"type"`
	Title               string `json:"title"`
	Content             string `json:"content"`
	AnswerR             string `json:"answer_r"`
	SingleReportPrompt  string `json:"single_report_prompt"`
	GeneralReportPrompt string `json:"general_report_prompt"`
}

// GlobalState 全局状态大篮子
type GlobalState struct {
	// 输入
	UserRequest string
	Knowledge   string

	// 中间状态：大纲列表
	Outline []string
	// 中间状态：当前执行到第几个了 (游标)
	CurrentIndex int
	// 中间状态：详细要求描述
	RequirementDesc string

	// 输出：最终汇总的结果
	Tasks []TaskItem

	// 模型
	LLM model.ChatModel
}

// ================= 2. 定义 Node (干活的节点) =================

// Planner: 负责根据用户需求拆解出大纲
func Planner(ctx context.Context, state *GlobalState) (*GlobalState, error) {
	fmt.Printf("\n🟦 [Planner] 收到需求: %s\n", state.UserRequest)

	ct := prompt.FromMessages(
		schema.FString,
		schema.SystemMessage("你是教学任务规划助手。根据用户需求和知识，先输出一个 JSON：{\"outline\": [字符串...], \"requirements\": 详细要求字符串}。严格 JSON，且仅输出该对象。"),
		schema.UserMessage("用户需求：{user_request}\n知识库：{knowledge}"),
	)
	msgs, err := ct.Format(ctx, map[string]any{
		"user_request": state.UserRequest,
		"knowledge":    state.Knowledge,
	})
	if err != nil {
		return nil, err
	}

	resp, err := state.LLM.Generate(ctx, msgs, model.WithTemperature(0.2))
	if err != nil {
		return nil, err
	}

	var p struct {
		Outline      []string `json:"outline"`
		Requirements string   `json:"requirements"`
	}
	if err := json.Unmarshal([]byte(resp.Content), &p); err != nil {
		return nil, fmt.Errorf("planner 解析失败: %w", err)
	}

	state.Outline = p.Outline
	state.RequirementDesc = p.Requirements
	state.CurrentIndex = 0
	state.Tasks = make([]TaskItem, 0)

	fmt.Printf("🟦 [Planner] 拆解出 %d 个任务，准备开始执行...\n", len(state.Outline))
	return state, nil
}

// Executor: 负责执行单个任务
func Executor(ctx context.Context, state *GlobalState) (*GlobalState, error) {
	// 1. 取出当前任务
	// 安全检查：防止索引越界（虽然 Condition 会保证，但防御性编程是个好习惯）
	if state.CurrentIndex >= len(state.Outline) {
		return state, nil
	}

	currentTopic := state.Outline[state.CurrentIndex]
	fmt.Printf("🔶 [Executor] 正在处理第 %d/%d 个任务: %s\n",
		state.CurrentIndex+1, len(state.Outline), currentTopic)

	ct := prompt.FromMessages(
		schema.FString,
		schema.SystemMessage("你是教学任务生成助手。只输出严格 JSON 对象，无额外文本或代码块。字段：sort(number)、type(number:1选择题/2填空题/3问答题)、title(string)、content(string,markdown)、answer_r(string)、single_report_prompt(string)、general_report_prompt(string)。"),
		schema.UserMessage("索引：{index}\n主题：{topic}\n详细要求：{requirements}\n请生成一个符合要求的任务。"),
	)
	msgs, err := ct.Format(ctx, map[string]any{
		"index":        state.CurrentIndex + 1,
		"topic":        currentTopic,
		"requirements": state.RequirementDesc,
	})
	if err != nil {
		return nil, err
	}

	resp, err := state.LLM.Generate(ctx, msgs, model.WithTemperature(0.3))
	if err != nil {
		return nil, err
	}

	var item TaskItem
	if err := json.Unmarshal([]byte(resp.Content), &item); err != nil {
		return nil, fmt.Errorf("executor 解析失败: %w", err)
	}

	// 2. 写入结果
	state.Tasks = append(state.Tasks, item)

	// 3. 关键步骤：游标自增
	state.CurrentIndex++

	return state, nil
}

// ================= 3. 定义 Condition (路由逻辑) =================

// ShouldLoop 标准的条件判断函数
// 返回值 string 对应的是 AddBranch map 中的 Key
func ShouldLoop(ctx context.Context, state *GlobalState) (string, error) {
	// 判断逻辑：如果当前索引 小于 总任务数，说明还有活没干完
	if state.CurrentIndex < len(state.Outline) {
		return "node_executor", nil
	}
	// 否则，结束
	return compose.END, nil
}

// ================= 4. 编排 Graph (主程序) =================

func main() {
	ctx := context.Background()

	llm, err := newChatModel(ctx)
	if err != nil {
		log.Fatalf("模型初始化错误: %v", err)
	}

	// 1. 初始化图
	g := compose.NewGraph[*GlobalState, *GlobalState]()

	// 2. 添加节点 (Node)
	_ = g.AddLambdaNode("node_planner", compose.InvokableLambda(Planner))
	_ = g.AddLambdaNode("node_executor", compose.InvokableLambda(Executor))

	// 3. 定义边 (Edge) - 静态流向
	// 只要 Start，就先去 Planner
	_ = g.AddEdge(compose.START, "node_planner")

	// 4. 定义分支 (Branch) - 动态流向
	loopBranch := compose.NewGraphBranch(ShouldLoop, map[string]bool{
		"node_executor": true,
		compose.END:     true,
	})

	// 重点来了！我们在两个地方挂载这个判断逻辑：

	// 位置 A: Planner 执行完后。
	// 原因：防止 Planner 生成了空列表，或者我们需要从第0个开始判断。
	_ = g.AddBranch("node_planner", loopBranch)

	// 位置 B: Executor 执行完后。
	// 原因：Executor 做完一个任务，索引+1了，必须再次判断是否还有下一个。
	// 如果有 -> "continue" -> 回到 node_executor (这就形成了环)
	// 如果无 -> "finish" -> 结束
	_ = g.AddBranch("node_executor", loopBranch)

	// 5. 编译运行
	runnable, err := g.Compile(ctx)
	if err != nil {
		log.Fatalf("编译错误: %v", err)
	}

	// 6. 构造输入
	inputState := GlobalState{
		UserRequest: "帮我生成一份 Golang 学习计划",
		Knowledge:   "这里是知识库内容...",
		LLM:         llm,
	}

	fmt.Println("🚀 Graph 开始运行...")
	finalState, err := runnable.Invoke(ctx, &inputState)
	if err != nil {
		log.Fatalf("运行错误: %v", err)
	}

	// 7. 展示结果
	fmt.Println("\n✅ 流程结束，最终合并结果:")
	printJSON(finalState.Tasks)
}

// 辅助函数：漂亮地打印 JSON
func printJSON(v interface{}) {
	b, _ := json.MarshalIndent(v, "", "  ")
	fmt.Println(string(b))
}

func newChatModel(ctx context.Context) (model.ChatModel, error) {
	apiKey := os.Getenv("LLM_API_KEY")
	baseURL := os.Getenv("LLM_BASE_URL")
	mdl := os.Getenv("LLM_MODEL")
	if apiKey == "" || baseURL == "" || mdl == "" {
		return nil, fmt.Errorf("缺少模型配置: 需要 LLM_API_KEY, LLM_BASE_URL, LLM_MODEL")
	}
	timeout := 60 * time.Second
	cm, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
		ByAzure:   false,
		BaseURL:   baseURL,
		APIKey:    apiKey,
		Timeout:   timeout,
		Model:     mdl,
		MaxTokens: nil,
	})
	if err != nil {
		return nil, err
	}
	return cm, nil
}
