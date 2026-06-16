# 理解LangChain

## 什么是LangChain?

LangChain是一个开源框架，用于开发由大型语言模型(LLM)驱动的应用程序。它提供了工具和组件来简化与LLM的交互，使开发者能够更轻松地构建复杂的AI应用。

## LangChain的核心概念

### 1. **模型(Models)**
- LLM提供商的集成（如OpenAI、Anthropic、Hugging Face等）
- 支持多种模型类型：聊天模型、文本补全模型等
- 统一的接口调用不同的模型

### 2. **提示模板(Prompt Templates)**
- 用于管理和格式化发送给LLM的提示
- 支持动态变量替换
- 便于提示的重用和管理

### 3. **链(Chains)**
- 连接多个操作的序列
- 例如：用户输入 → 提示模板 → LLM → 输出解析
- 可以创建复杂的多步骤工作流

### 4. **记忆(Memory)**
- 管理对话历史
- 支持不同类型的记忆机制（缓冲、摘要等）
- 让应用能够记住上下文信息

### 5. **检索(Retrieval)**
- 从外部数据源获取相关信息
- 支持向量数据库、文档加载器等
- 实现RAG（检索增强生成）功能

### 6. **代理(Agents)**
- 让LLM能够使用工具和进行推理
- 支持自主决策和多步规划
- 可以集成外部API和函数

---

## 如何构建一个智能体（Agent）

### 什么是Agent？

Agent（智能体/代理）是一个能够**自主决策**的AI系统。它不像普通Chain那样按固定顺序执行步骤，而是由LLM决定"下一步该做什么"——调用哪个工具、是否需要更多信息、何时给出最终答案。

### Agent的核心组件

```
                  ┌─────────────┐
                  │   用户输入   │
                  └──────┬──────┘
                         ▼
                  ┌─────────────┐
                  │  LLM (大脑) │◄──── 决定下一步行动
                  └──────┬──────┘
                         ▼
              ┌───────────────────┐
              │   Agent执行器     │
              │  (AgentExecutor)  │
              └───┬───┬───┬───┬──┘
                  │   │   │   │
         ┌────────┘   │   │   └────────┐
         ▼            ▼   ▼            ▼
     ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
     │ 工具1  │ │ 工具2  │ │ 工具3  │ │ 工具4  │
     │(搜索)  │ │(计算器)│ │(API调用)│ │(数据库)│
     └────────┘ └────────┘ └────────┘ └────────┘
```

1. **LLM（大脑）** — 负责推理和决策
2. **工具(Tools)** — Agent可以调用的外部能力
3. **提示模板(Prompt)** — 指导Agent行为的系统指令
4. **执行器(AgentExecutor)** — 循环调度：思考→行动→观察→再思考...

### Agent的工作流程

```
循环：
  1. 思考 (Thought)  — LLM分析当前情况
  2. 行动 (Action)   — 选择并调用一个工具
  3. 观察 (Observation) — 获取工具返回结果
  4. 重复以上步骤，直到LLM决定给出最终答案
```

### 构建Agent的步骤

#### 步骤1：定义工具（Tools）

工具是Agent与外部世界交互的接口。

```python
from langchain.tools import tool
import requests

# 方式一：使用装饰器定义工具
@tool
def search_web(query: str) -> str:
    """搜索互联网获取最新信息"""
    # 模拟搜索功能
    return f"关于'{query}'的搜索结果..."

# 方式二：定义更复杂的工具
@tool
def calculate(expression: str) -> str:
    """执行数学计算"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"

# 方式三：使用预定义工具
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

wikipedia = WikipediaQueryRun(
    api_wrapper=WikipediaAPIWrapper()
)
```

#### 步骤2：创建Agent

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor

# 初始化LLM
llm = ChatOpenAI(model="gpt-4", temperature=0)

# 整理工具列表
tools = [search_web, calculate, wikipedia]

# 创建提示模板
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有用的AI助手，可以使用工具来回答问题。"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# 创建Agent
agent = create_tool_calling_agent(llm, tools, prompt)

# 创建执行器
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,   # 打印思考过程
    handle_parsing_errors=True  # 处理解析错误
)
```

#### 步骤3：运行Agent

```python
# 运行Agent
result = agent_executor.invoke({
    "input": "计算 1234 * 5678 的结果，然后查一下Python是什么"
})
print(result["output"])
```

### 完整示例：多功能助手Agent

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from datetime import datetime

# ----- 1. 定义工具 -----

@tool
def get_current_time_and_date() -> str:
    """获取当前日期和时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def calculate(expression: str) -> str:
    """执行数学计算，如 '1 + 2 * 3'"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"

@tool
def get_city_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    # 这里可以接入真实的天气API
    weather_data = {
        "北京": "25°C, 晴朗",
        "上海": "28°C, 多云",
        "深圳": "30°C, 阵雨",
    }
    return weather_data.get(city, f"暂无{city}的天气数据")

# ----- 2. 创建Agent -----

llm = ChatOpenAI(model="gpt-4", temperature=0)
tools = [get_current_time_and_date, calculate, get_city_weather]

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个多功能AI助手。你可以计算、查询时间、查天气。请根据问题选择合适的工具。"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

# ----- 3. 运行Agent -----

if __name__ == "__main__":
    questions = [
        "现在几点？",
        "计算 (12 + 34) * 56 的结果",
        "北京今天天气怎么样？",
    ]
    for q in questions:
        print(f"\n用户: {q}")
        result = agent_executor.invoke({"input": q})
        print(f"助手: {result['output']}")
```

### 运行示例输出

```
用户: 现在几点？
> 思考：用户想知道当前时间，我需要调用 get_current_time_and_date 工具
> 行动：调用 get_current_time_and_date()
> 观察：2026-06-14 15:30:00
助手: 当前时间是 2026年6月14日 15:30。

用户: 计算 (12 + 34) * 56 的结果
> 思考：这是一个数学计算，使用 calculate 工具
> 行动：调用 calculate("(12 + 34) * 56")
> 观察：(12 + 34) * 56 = 2576
助手: (12 + 34) * 56 = 2576

用户: 北京今天天气怎么样？
> 思考：用户查询北京天气，调用 get_city_weather 工具
> 行动：调用 get_city_weather("北京")
> 观察：25°C, 晴朗
助手: 北京今天天气：25°C，晴朗。
```

### Agent的类型

| Agent类型 | 特点 | 适用场景 |
|-----------|------|----------|
| **Tool Calling Agent** | LLM原生支持工具调用（推荐） | GPT-4、Claude等支持tool calling的模型 |
| **ReAct Agent** | 通过提示模板实现思考-行动-观察循环 | 不支持tool calling的模型 |
| **OpenAI Tools Agent** | 专为OpenAI工具调用优化 | 使用OpenAI系列模型 |
| **Structured Chat Agent** | 支持多参数工具调用 | 需要复杂工具参数时 |
| **Conversational Agent** | 带记忆功能的对话Agent | 聊天机器人场景 |

### Agent的高级用法

#### 1. 带记忆的Agent

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
)
```

#### 2. 自定义系统提示

```python
system_prompt = """你是一个专业的数据分析助手。你可以：
1. 使用搜索引擎查找数据
2. 使用Python工具分析数据
3. 使用计算器进行计算
4. 使用图表工具生成可视化

请逐步分析问题，并在每一步解释你的思考过程。

可用工具：{tools}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])
```

#### 3. 限制最大迭代次数

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    max_iterations=5,        # 最大思考-行动循环次数
    max_execution_time=60,   # 最大执行时间（秒）
    early_stopping_method="generate",  # 超时后直接生成回答
)
```

### 构建Agent的最佳实践

1. **工具命名要清晰** — 函数名和描述应让LLM能理解用途
2. **提供详细的工具描述** — docstring是LLM理解工具的关键
3. **设置合理的限制** — 最大迭代次数和执行时间
4. **处理错误 gracefully** — 使用 `handle_parsing_errors=True`
5. **开启 verbose 模式调试** — 在开发阶段观察Agent的思考过程
6. **工具返回值要结构化** — 清晰的返回值让LLM更容易处理
7. **单一职责原则** — 每个工具只做一件事，但要做好

### 注意事项

- Agent的智能程度取决于底层的LLM能力
- 工具调用可能有安全风险，要做好输入验证
- Agent可能陷入循环或产生幻觉，需要设置防护措施
- 实际生产中使用真实API（天气、搜索等）需要API Key

---

## LangChain的主要优势

1. **模块化设计** - 灵活组合不同的组件
2. **多模型支持** - 轻松切换不同的LLM提供商
3. **完整工具链** - 涵盖开发AI应用的全套需求
4. **活跃社区** - 不断更新和完善的开源项目
5. **丰富的集成** - 与数据库、搜索引擎等工具集成

## 快速开始

### 安装
```bash
pip install langchain openai
```

### 基础示例
```python
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# 初始化LLM
llm = OpenAI(api_key="your-api-key")

# 创建提示模板
template = "请用一句话解释{topic}"
prompt = PromptTemplate(input_variables=["topic"], template=template)

# 创建链
chain = LLMChain(llm=llm, prompt=prompt)

# 运行链
result = chain.run(topic="机器学习")
print(result)
```

## LangChain的常见应用场景

1. **聊天应用** - 构建带有记忆的对话系统
2. **问答系统** - 基于文档的QA应用
3. **内容生成** - 自动化内容创作
4. **数据分析助手** - 帮助用户分析和理解数据
5. **代码助手** - AI编程辅助工具
6. **信息检索** - 智能搜索和信息提取

## 学习资源

- **官方文档**: https://python.langchain.com/
- **GitHub仓库**: https://github.com/hwchase17/langchain
- **社区论坛**: Discord社区

## 总结

LangChain通过提供标准化的接口和强大的工具库，大大降低了开发LLM应用的复杂性。无论是简单的文本生成还是复杂的多步骤AI系统，LangChain都能提供必要的支持。

