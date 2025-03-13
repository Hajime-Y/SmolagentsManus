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
from scripts.file_editor import FileEditorTool
from scripts.bash_tool import BashTool

from smolagents import (
    # CodeAgent,
    GoogleSearchTool,
    # HfApiModel,
    # LiteLLMModel,
    ToolCallingAgent,
    Model
)

def create_search_agent(model: Model, text_limit: int = 100000):
    # ブラウザマネージャーとツールの設定
    browser_manager = BrowserManager(headless=False)
    browser_tools = [
        GoogleSearchTool(provider="serper"),
        BrowserNavigationTool(browser_manager),
        BrowserClickTool(browser_manager),
        BrowserInputTextTool(browser_manager),
        BrowserGetHtmlTool(browser_manager),
        BrowserGetTextTool(browser_manager),
        BrowserScrollTool(browser_manager),
        BrowserExecuteJsTool(browser_manager),
        BrowserScreenshotTool(browser_manager),
        BrowserSwitchTabTool(browser_manager),
        BrowserNewTabTool(browser_manager),
        BrowserCloseTabTool(browser_manager),
        BrowserRefreshTool(browser_manager),
        TextInspectorTool(model, text_limit=text_limit),
        FileEditorTool(),
        BashTool(),
    ]

    # search agentの作成
    search_agent = ToolCallingAgent(
        model=model,
        tools=browser_tools,
        max_steps=20,
        verbosity_level=2,
        planning_interval=4,
        name="search_agent",
        description="""A team member that will search the internet to find information online.
        Ask him to navigate websites, interact with web elements, and gather data from various sources.
        Provide him with detailed context for your queries to help him search more effectively.
        He can handle complex tasks like comparing information across different websites.
        Your request must be a real sentence, not a google search! Like "Find me this information (...)" rather than a few keywords.""",
        # 日本語訳：
        # オンライン情報を検索するチームメンバーです。
        # ウェブサイトの閲覧、Web要素との対話、様々なソースからのデータ収集の依頼ができます。
        # より効果的な検索のため、クエリに関する詳細なコンテキストを提供してください。
        # 異なるウェブサイト間の情報比較など、複雑なタスクも処理できます。
        # 検索キーワードではなく、「この情報を探して(...)」のような自然な文章で依頼してください。
        provide_run_summary=True,
    )
    search_agent.prompt_templates["managed_agent"]["task"] += """You can navigate to .txt online files.
    If a non-html page is in another format, especially .pdf or a Youtube video, use tool 'inspect_file_as_text' to inspect it.
    Additionally, if after some searching you find out that you need more information to answer the question, you can use `final_answer` with your request for clarification as argument to request for more information."""
    # 日本語訳：
    # テキスト形式のオンラインファイルを閲覧できます。
    # 非HTMLページが他の形式（特に.pdfやYoutube動画）の場合、'inspect_file_as_text'ツールを使用して確認してください。
    # 検索後、質問に対する情報が不足している場合、`final_answer`を使用して追加の情報を要求することもできます。
    
    return search_agent