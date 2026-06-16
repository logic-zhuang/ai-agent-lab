"""
================================================================================
                    我的个人智能体 (My Personal Agent)
================================================================================
基于 LangChain 1.3+ 构建的多功能 AI 助手，支持：
  - 数学计算 / 文件信息查询 / 当前日期时间
  - 文本统计 / 文件搜索 / AI 对话
  - 对话记忆（记住上下文）
  - 可切换后端：DeepSeek / OpenAI / Ollama 本地模型 / 内置推理

使用方法：
  1. 复制 .env.example 为 .env，填入你的 API Key：
       # 推荐：DeepSeek（便宜好用）
       LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
       LLM_MODEL=deepseek-chat
       LLM_BASE_URL=https://api.deepseek.com

       # 或使用 OpenAI
       # LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
       # LLM_MODEL=gpt-4o-mini
       # LLM_BASE_URL=https://api.openai.com/v1
  
  2. 如需使用本地 Ollama，确保 Ollama 正在运行：
       https://ollama.ai/
  
  3. 运行：python my_agent.py
================================================================================
"""

import os
import json
import math
import datetime
import re
from typing import Optional
from pathlib import Path

# ============================================================================
# 依赖导入
# ============================================================================
try:
    from langchain.tools import tool
    from langchain.agents import create_agent
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain.chat_models import init_chat_model
    from langchain_core.tools import BaseTool
    from dotenv import load_dotenv
except ImportError as e:
    print(f"[错误] 缺少依赖包: {e}")
    print("请运行: pip install langchain langchain-community langchain-openai python-dotenv")
    exit(1)

# 加载 .env 文件中的环境变量
load_dotenv()


# ============================================================================
# 第一步：定义工具 (Tools) —— 智能体的"手脚"
# ============================================================================

@tool
def calculate(expression: str) -> str:
    """执行数学计算，支持 + - * / ** % 等运算。例如: '(12 + 34) * 56'"""
    try:
        allowed_names = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow, "int": int, "float": float,
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
            "tan": math.tan, "pi": math.pi, "e": math.e,
        }
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"


@tool
def get_current_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """获取当前日期和时间。可指定格式，默认 '%Y-%m-%d %H:%M:%S'"""
    return datetime.datetime.now().strftime(format_str)


@tool
def get_file_info(file_path: str) -> str:
    """获取文件信息：大小、修改时间、行数等。参数为文件路径。"""
    path = Path(file_path)
    if not path.exists():
        return f"文件不存在: {file_path}"
    stat = path.stat()
    size_kb = stat.st_size / 1024
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    info = [
        f"📄 文件名: {path.name}",
        f"📁 路径: {path.absolute()}",
        f"📏 大小: {size_kb:.2f} KB",
        f"🕐 修改时间: {mtime}",
    ]
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.count("\n") + 1
        chars = len(text)
        info.append(f"📝 行数: {lines}")
        info.append(f"🔤 字符数: {chars}")
    except Exception:
        info.append("⚠️ 二进制文件或无法读取")
    return "\n".join(info)


@tool
def list_directory(dir_path: str = ".") -> str:
    """列出指定目录下的文件和文件夹。参数为目录路径，默认为当前目录。"""
    path = Path(dir_path)
    if not path.exists():
        return f"目录不存在: {dir_path}"
    if not path.is_dir():
        return f"不是目录: {dir_path}"

    items = []
    for item in path.iterdir():
        if item.is_dir():
            items.append(f"  📁 {item.name}/")
        else:
            size = item.stat().st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/1024/1024:.1f} MB"
            items.append(f"  📄 {item.name} ({size_str})")

    if not items:
        return "目录为空"

    header = f"📂 {path.absolute()} 的内容 ({len(items)} 项):\n"
    return header + "\n".join(items)


@tool
def count_words(text: str) -> str:
    """统计文本中的字数、字符数（含/不含空格）。"""
    char_count = len(text)
    char_no_space = len(text.replace(" ", "").replace("\n", ""))
    word_count = len(text.split())
    line_count = text.count("\n") + 1
    return (
        f"📊 文本统计:\n"
        f"  • 单词/词数: {word_count}\n"
        f"  • 字符数(含空格): {char_count}\n"
        f"  • 字符数(不含空格): {char_no_space}\n"
        f"  • 行数: {line_count}"
    )


@tool
def search_text(file_path: str, keyword: str) -> str:
    """在文件中搜索关键字。参数: file_path=文件路径, keyword=搜索关键词"""
    path = Path(file_path)
    if not path.exists():
        return f"文件不存在: {file_path}"
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.split("\n")
        matches = []
        for i, line in enumerate(lines, 1):
            if keyword.lower() in line.lower():
                start = max(0, i - 2)
                end = min(len(lines), i + 1)
                context = lines[start:end]
                matches.append(f"--- 第 {i} 行 ---\n" + "\n".join(context))
        if matches:
            return f"找到 {len(matches)} 处匹配:\n\n" + "\n\n".join(matches)
        else:
            return f"在 '{path.name}' 中未找到 '{keyword}'"
    except Exception as e:
        return f"搜索失败: {e}"


# ============================================================================
# 第二步：组装智能体
# ============================================================================

class MyAgent:
    """我的个人智能体"""

    def __init__(self, backend: str = "auto"):
        self.backend = backend
        self.tools = [
            calculate,
            get_current_time,
            get_file_info,
            list_directory,
            count_words,
            search_text,
        ]
        self.chat_history = []  # [(role, content), ...]
        self.llm = self._init_llm(backend)
        self.agent = None

        if self.llm:
            self._setup_agent()

    def _init_llm(self, backend: str):
        """初始化 LLM（支持 DeepSeek / OpenAI / Ollama）"""
        # 统一的环境变量配置
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        model_name = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL", "deepseek-chat")

        try:
            # --- DeepSeek / OpenAI（兼容 OpenAI 格式的 API） ---
            if backend in ("deepseek", "openai") or (backend == "auto" and api_key):
                provider = "DeepSeek" if ("deepseek" in (base_url or "")) or (backend == "deepseek") else "OpenAI"
                print(f"[信息] 使用 {provider} 后端 ({model_name})")
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model_name,
                    temperature=0.3,
                    api_key=api_key,
                    base_url=base_url,
                )

            # --- Ollama 本地模型 ---
            if backend == "ollama" or backend == "auto":
                model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
                print(f"[信息] 尝试使用 Ollama 本地模型 ({model_name})")
                model_str = f"ollama:{model_name}"
                llm = init_chat_model(model_str, temperature=0.3)
                llm.invoke("test")
                return llm

        except Exception as e:
            if backend != "auto":
                print(f"[警告] {backend} 后端启动失败: {e}")
                print("将回退到内置推理模式")

        print("[信息] 使用内置推理引擎（无需 API Key）")
        return None

    def _setup_agent(self):
        """使用 LangChain 新版 create_agent API"""
        system_prompt = SystemMessage(
            '你是一个多功能AI助手，名字叫"小卢同学"。\n'
            "你拥有以下能力:\n"
            "- 数学计算\n"
            "- 文件/目录信息查询\n"
            "- 文本统计\n"
            "- 文件内容搜索\n"
            "- 获取当前时间\n\n"
            "请根据用户问题选择合适的工具，给出详细的解答。\n"
            "如果工具返回的结果不够，可以追问或尝试其他工具。\n"
            "回答尽量简洁清晰。"
        )

        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
            name="xiaoling",
        )

    def _mock_reason(self, user_input: str) -> str:
        """内置推理引擎：通过规则匹配模拟智能体行为"""
        input_lower = user_input.lower()
        now = datetime.datetime.now()

        # 1) 问候
        if any(greet in input_lower for greet in ["你好", "hello", "hi", "早上好", "晚上好", "嗨"]):
            hour = now.hour
            if 5 <= hour < 12:
                greeting = "早上好"
            elif 12 <= hour < 14:
                greeting = "中午好"
            elif 14 <= hour < 18:
                greeting = "下午好"
            else:
                greeting = "晚上好"
            return (
                f'{greeting}！👋 我是你的个人智能体"小灵"。\n\n'
                "我可以帮你:\n"
                "  1️⃣ 数学计算  → 试试: 计算 15 * 27 + 8\n"
                "  2️⃣ 文件信息  → 试试: 查看 my_agent.py 的信息\n"
                "  3️⃣ 目录列表  → 试试: 列出当前目录\n"
                "  4️⃣ 文本统计  → 试试: 统计 hello world 的字数\n"
                "  5️⃣ 文件搜索  → 试试: 在 my_agent.py 中搜索 tool\n"
                "  6️⃣ 当前时间  → 试试: 现在几点\n"
                "\n输入 help 查看所有功能。"
            )

        # 2) 帮助
        if input_lower in ["help", "帮助", "h", "?", "功能"]:
            return (
                "📋 **可用功能列表**\n\n"
                "🔢 **计算**     — 计算数学表达式\n"
                "   例: 计算 (15+3)*7\n\n"
                "📂 **文件信息**  — 查看文件详情\n"
                "   例: 查看 my_agent.py 的信息\n\n"
                "📁 **目录列表**  — 列出文件夹内容\n"
                "   例: 列出当前目录\n\n"
                "📊 **文本统计**  — 统计字符/单词数\n"
                "   例: 统计 Hello World 的字数\n\n"
                "🔍 **文件搜索**  — 在文件中搜索关键词\n"
                "   例: 在 my_agent.py 中搜索 tool\n\n"
                "🕐 **当前时间**  — 显示当前日期时间\n"
                "   例: 现在几点\n\n"
                "💡 **提示**: 在 .env 中填入 LLM_API_KEY 可使用 AI 对话！"
            )

        # 3) 时间
        if any(w in input_lower for w in ["时间", "几点", "日期", "date", "time", "现在"]):
            return f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}"

        # 4) 计算
        calc_patterns = [
            r"计算\s*(.+?)(?:[。！？\.\!\?]|$)",
            r"算一下\s*(.+?)(?:[。！？\.\!\?]|$)",
        ]
        for pattern in calc_patterns:
            m = re.search(pattern, user_input)
            if m:
                expr = m.group(1).strip()
                result = calculate.invoke({"expression": expr})
                return f"计算结果: {result}"

        if re.search(r'[\d\+\-\*\/\(\)]', user_input) and len(user_input) < 50:
            exprs = re.findall(r'[\d\+\-\*\/\(\)\%\.\^]+', user_input)
            for expr in exprs:
                if len(expr) >= 3:
                    expr_clean = expr.replace('^', '**')
                    result = calculate.invoke({"expression": expr_clean})
                    if "错误" not in result:
                        return f"计算结果: {result}"

        # 5) 文件信息
        file_match = re.search(r"(?:查看|文件|打开|读取|read|info)\s*(.+?\.\w+)", user_input)
        if file_match:
            return get_file_info.invoke({"file_path": file_match.group(1).strip()})

        # 6) 目录
        if any(w in input_lower for w in ["目录", "文件夹", "列表", "文件列表", "ls", "dir"]):
            dir_match = re.search(r"(?:目录|文件夹|列表)\s*(.+?)(?:[。！？]|$)", user_input)
            if dir_match:
                return list_directory.invoke({"dir_path": dir_match.group(1).strip()})
            return list_directory.invoke({"dir_path": "."})

        # 7) 统计字数
        count_match = re.search(r"(?:统计|字数|count)\s*(.+?)(?:[。！？]|$)", user_input)
        if count_match:
            text = count_match.group(1).strip().strip("'\"")
            if text and len(text) < 200:
                return count_words.invoke({"text": text})

        # 8) 文件搜索
        search_match = re.search(
            r"在\s*(.+?\.\w+)\s*(?:中|里)?\s*搜索\s*(.+?)(?:[。！？]|$)",
            user_input,
        )
        if search_match:
            return search_text.invoke({
                "file_path": search_match.group(1).strip(),
                "keyword": search_match.group(2).strip(),
            })

        # 9) 默认回复
        self.chat_history.append(("user", user_input))
        return (
            f'你说的是 "{user_input}" 对吗？\n'
            "我目前可用的功能:\n"
            "  - 输入「计算 表达式」进行数学计算\n"
            "  - 输入「查看 文件名」查看文件信息\n"
            "  - 输入「列出目录」浏览文件夹\n"
            "  - 输入「统计 文本」统计字数\n"
            "  - 输入「在 文件中 搜索 关键词」搜索内容\n"
            "  - 输入「现在几点」查看时间\n\n"
            "💡 如需 AI 对话，在 .env 中填入 LLM_API_KEY 后重启即可！"
        )

    def chat(self, user_input: str) -> str:
        """处理用户输入并返回回复"""
        user_input = user_input.strip()
        if not user_input:
            return "请输入你想问的问题！"

        if user_input.lower() in ["exit", "quit", "退出", "再见", "拜拜"]:
            return "再见！👋 期待下次见面~"

        if user_input.lower() in ["clear", "重置", "清空"]:
            self.chat_history = []
            return "✅ 对话记忆已清空！"

        # 使用 LLM Agent
        if self.agent:
            try:
                messages = []
                for role, content in self.chat_history:
                    if role == "user":
                        messages.append(HumanMessage(content=content))
                    else:
                        messages.append(AIMessage(content=content))
                messages.append(HumanMessage(content=user_input))

                result = self.agent.invoke({"messages": messages})
                response = result["messages"][-1].content

                self.chat_history.append(("user", user_input))
                self.chat_history.append(("assistant", response))
                return response
            except Exception as e:
                return f"处理出错: {e}\n\n已回退到内置推理模式。"
                self.agent = None

        # 使用内置推理引擎
        response = self._mock_reason(user_input)
        self.chat_history.append(("user", user_input))
        self.chat_history.append(("assistant", response))
        return response

    def show_welcome(self):
        """显示欢迎信息"""
        version = "LLM版" if self.llm else "内置推理版"
        print("=" * 60)
        print("            🤖  我的个人智能体 - 小灵")
        print("=" * 60)
        print(f"  模式: {version}  |  工具: {len(self.tools)} 个可用")
        print(f"  输入 help 查看帮助  |  exit 退出")
        print("-" * 60)
        print("  你好！有什么我可以帮你的吗？")
        print("=" * 60)

    def run_interactive(self):
        """启动交互式对话"""
        self.show_welcome()
        while True:
            try:
                user_input = input("\n💬 你: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit", "退出"]:
                    print("\n🤖 小灵: 再见！👋 期待下次见面~")
                    break
                response = self.chat(user_input)
                print(f"\n🤖 小灵: {response}")
            except KeyboardInterrupt:
                print("\n\n🤖 小灵: 再见！👋")
                break
            except Exception as e:
                print(f"\n[错误] {e}")


# ============================================================================
# 第三步：主入口
# ============================================================================

def main():
    import sys

    backend = "auto"
    single_query = None

    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--backend" and i + 1 < len(args):
            backend = args[i + 1]
        elif arg == "--query" and i + 1 < len(args):
            single_query = args[i + 1]
        elif arg in ["--help", "-h"]:
            print("用法: python my_agent.py [选项]")
            print("")
            print("选项:")
            print("  --backend auto|deepseek|openai|ollama   选择 AI 后端")
            print('  --query "你的问题"                      单次查询模式')
            print("  --help                                  显示此帮助")
            print("")
            print("环境变量 (在 .env 文件中设置):")
            print("  LLM_API_KEY=sk-xxx    API Key（支持 DeepSeek / OpenAI）")
            print("  LLM_MODEL=deepseek-chat  模型名称")
            print("  LLM_BASE_URL=https://api.deepseek.com  API 地址")
            print("")
            print("示例:")
            print("  python my_agent.py")
            print('  python my_agent.py --query "计算 15 * 24"')
            print('  python my_agent.py --backend deepseek --query "你好"')
            return

    agent = MyAgent(backend=backend)

    if single_query:
        response = agent.chat(single_query)
        print(response)
    else:
        agent.run_interactive()


if __name__ == "__main__":
    main()
