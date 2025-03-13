from smolagents import (
    CodeAgent,
    Model
)

# from scripts.text_inspector_tool import TextInspectorTool
from scripts.file_editor import FileEditorTool
from scripts.bash_tool import BashTool

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

def create_code_agent(model: Model):
    # ツールの設定
    code_tools = [
        FileEditorTool(),
        BashTool(),
    ]

    # code agentの作成
    code_agent = CodeAgent(
        model=model,
        tools=code_tools,
        max_steps=20,
        verbosity_level=2,
        additional_authorized_imports=AUTHORIZED_IMPORTS,
        planning_interval=4,
        name="code_agent",
        description="""A team member specialized in software engineering tasks.
        Ask him to analyze code, suggest improvements, debug issues, and provide coding guidance.
        He understands multiple programming languages and software development best practices.
        He can help with code reviews, architecture decisions, and technical documentation.
        He can write and execute Python code to verify solutions and demonstrate implementations.
        Provide him with code context and specific requirements for better assistance.""",
        # 日本語訳：
        # ソフトウェアエンジニアリングタスクを専門とするチームメンバーです。
        # コードの分析、改善提案、デバッグ、およびコーディングガイダンスの依頼ができます。
        # 複数のプログラミング言語とソフトウェア開発のベストプラクティスを理解しています。
        # コードレビュー、アーキテクチャの決定、技術文書作成をサポートします。
        # Pythonコードを作成・実行して、解決策の検証やデモンストレーションが可能です。
        # より良いサポートのため、コードのコンテキストと具体的な要件を提供してください。
        provide_run_summary=True,
    )
    
    code_agent.prompt_templates["managed_agent"]["task"] += """If you need more information about the code or requirements to complete the task, you can use `final_answer` with your request for clarification as argument to ask for more details.
    When analyzing code, consider best practices, potential bugs, and optimization opportunities.
    You can suggest refactoring when appropriate and explain the benefits of your proposed changes."""
    # 日本語訳：
    # タスクを完了するためにコードや要件についてさらに情報が必要な場合は、`final_answer`を使用して詳細を求めることができます。
    # コードを分析する際は、ベストプラクティス、潜在的なバグ、最適化の機会を考慮してください。
    # 適切な場合はリファクタリングを提案し、提案した変更の利点を説明してください。
    
    return code_agent 