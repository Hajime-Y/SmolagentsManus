from typing import Optional
from smolagents import Tool
import os
import aiofiles

class FileServerTool(Tool):
    name = "file_server"
    description = """
Save content to a local file at a specified path.
Use this tool when you need to save text, code, or generated content to a file on the local filesystem.
The tool accepts content and a file path, and saves the content to that location."""
# 日本語訳：
# 指定されたパスにローカルファイルとしてコンテンツを保存します。
# テキスト、コード、生成されたコンテンツをローカルファイルシステムに保存する必要がある場合に
# このツールを使用してください。
# このツールは、コンテンツとファイルパスを受け取り、指定された場所にコンテンツを保存します。

    inputs = {
        "file_path": {
            "description": "The path where the file should be saved, including filename and extension.",
            "type": "string",
        },
        "content": {
            "description": "The content to save to the file.",
            "type": "string",
        },
        "mode": {
            "description": "[Optional]: The file opening mode. Default is 'w' for write. Use 'a' for append.",
            "type": "string",
            "nullable": True,
        },
    }
    output_type = "string"

    async def forward(self, file_path: str, content: str, mode: Optional[str] = "w") -> str:
        try:
            # Ensure the directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            # Write directly to the file
            async with aiofiles.open(file_path, mode, encoding="utf-8") as file:
                await file.write(content)

            return f"Content successfully saved to {file_path}"
        except Exception as e:
            return f"Error saving file: {str(e)}"