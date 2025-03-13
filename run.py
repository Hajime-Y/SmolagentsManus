# run.py
# reference: https://github.com/huggingface/smolagents/blob/main/examples/open_deep_research/run.py

import argparse
import os
import threading

from dotenv import load_dotenv
from huggingface_hub import login
from scripts.text_inspector_tool import TextInspectorTool
from scripts.browser_use_tool import (
    BrowserManager,
    BrowserNavigationTool,
    BrowserClickTool,
    BrowserInputTextTool,
    BrowserGetHtmlTool,
    BrowserGetTextTool,
    BrowserScrollTool,
    BrowserExecuteJsTool,
    BrowserScreenshotTool,
    BrowserSwitchTabTool,
    BrowserNewTabTool,
    BrowserCloseTabTool,
    BrowserRefreshTool,
)
from scripts.visual_qa import visualizer
from agents.search_agent import create_search_agent
from agents.code_agent import create_code_agent
from smolagents import (
    CodeAgent,
    # GoogleSearchTool,  # 削除
    # HfApiModel,
    LiteLLMModel,
    # ToolCallingAgent,  # 削除
    UserInputTool
)

# 1. まずBrowserManagerインスタンスを作成
browser_manager = BrowserManager(headless=False)

# 2. 全てのブラウザツールを作成
BROWSER_TOOLS = [
    BrowserNavigationTool(browser_manager),  # VisitToolの代替
    BrowserClickTool(browser_manager),
    BrowserInputTextTool(browser_manager),
    BrowserGetHtmlTool(browser_manager),
    BrowserGetTextTool(browser_manager),
    BrowserScrollTool(browser_manager),      # PageUpTool, PageDownToolの代替
    BrowserExecuteJsTool(browser_manager),
    BrowserScreenshotTool(browser_manager),
    BrowserSwitchTabTool(browser_manager),
    BrowserNewTabTool(browser_manager),
    BrowserCloseTabTool(browser_manager),
    BrowserRefreshTool(browser_manager),
]


AUTHORIZED_IMPORTS = [
    "requests",
    "zipfile",
    "os",
    "pandas",
    "numpy",
    "sympy",
    "json",
    "bs4",
    "pubchempy",
    "xml",
    "yahoo_finance",
    "Bio",
    "sklearn",
    "scipy",
    "pydub",
    "io",
    "PIL",
    "chess",
    "PyPDF2",
    "pptx",
    "torch",
    "datetime",
    "fractions",
    "csv",
    "matplotlib",
    "seaborn",
    "plotly",
]
load_dotenv(override=True)
login(os.getenv("HF_TOKEN"))

append_answer_lock = threading.Lock()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "question", type=str, help="for example: 'How many studio albums did Mercedes Sosa release before 2007?'"
    )
    parser.add_argument("--model-id", type=str, default="o1")
    return parser.parse_args()


custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"

BROWSER_CONFIG = {
    "viewport_size": 1024 * 5,
    "downloads_folder": "downloads_folder",
    "request_kwargs": {
        "headers": {"User-Agent": user_agent},
        "timeout": 300,
    },
    "serpapi_key": os.getenv("SERPAPI_API_KEY"),
}

os.makedirs(f"./{BROWSER_CONFIG['downloads_folder']}", exist_ok=True)


def create_agent(model_id="o3-mini"):
    model_params = {
        "model_id": model_id,
        "custom_role_conversions": custom_role_conversions,
        "max_completion_tokens": 8192,
    }
    if model_id == "o3-mini":
        model_params["reasoning_effort"] = "high"
    model = LiteLLMModel(**model_params)

    text_limit = 100000
    
    # search_agentを取得
    search_agent = create_search_agent(model)

    # code_agentを取得
    code_agent = create_code_agent(model)
    
    manager_agent = CodeAgent(
        model=model,
        tools=[visualizer, TextInspectorTool(model, text_limit), UserInputTool()],
        max_steps=20,
        verbosity_level=2,
        additional_authorized_imports=AUTHORIZED_IMPORTS,
        planning_interval=4,
        managed_agents=[search_agent, code_agent],
    )
    
    # manager_agentのプロンプトを追加
    manager_agent.prompt_templates["system_prompt"] += """
    As a manager agent, your primary role is to coordinate and delegate tasks to your specialized agents.
    Focus on planning, task distribution, and synthesizing information from your managed agents.
    Delegate search tasks to the search agent and code-related tasks to the code agent whenever possible.
    If you need clarification about the task requirements, you can use `user_input` with your request for clarification.
    Avoid performing specialized tasks yourself when they can be handled by your managed agents.
    
    CRITICAL CONSTRAINT: You MUST create all plans AND generate all outputs in the same language as the user's input.
    For example, if the user's query is in Japanese, you MUST create your plans and provide all responses in Japanese as well.
    """
    # 日本語訳：
    # マネージャーエージェントとして、あなたの主な役割は専門エージェントの調整とタスクの委任です。
    # 計画、タスク分配、および管理下のエージェントからの情報の統合に集中してください。
    # 可能な限り、検索タスクはsearch agentに、コード関連のタスクはcode agentに委任してください。
    # タスクの要件について明確化が必要な場合は、`user_input`を使用して詳細を求めることができます。
    # 管理下のエージェントが処理できる専門的なタスクを自分で実行することは避けてください。
    # 
    # 重要な制約：あなたは必ずユーザーの入力と同じ言語でプランの作成と出力を行わなくてはならない。
    # 例えば、ユーザーの質問が日本語の場合は、必ず計画も応答もすべて日本語で提供してください。

    return manager_agent


def main():
    args = parse_args()

    agent = create_agent(model_id=args.model_id)

    answer = agent.run(args.question)

    print(f"Got this answer: {answer}")


if __name__ == "__main__":
    main()