from typing import Optional, List, Union, get_args
from smolagents import Tool
import os
import aiofiles
from pathlib import Path

# Literal型の代わりにstr型を使用
# Command = Literal[
#     "view",
#     "create",
#     "str_replace",
#     "insert",
#     "undo_edit",
# ]

# 代わりに有効なコマンドのリストを定義
VALID_COMMANDS = ["view", "create", "str_replace", "insert", "undo_edit"]

SNIPPET_LINES: int = 4
MAX_RESPONSE_LEN: int = 16000
TRUNCATED_MESSAGE: str = "<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>"

class FileEditorTool(Tool):
    name = "file_editor"
    description = """Custom editing tool for viewing, creating and editing files
* State is persistent across command calls and discussions with the user
* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* The `undo_edit` command will revert the last edit made to the file at `path`

Notes for using the `str_replace` command:
* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!
* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique
* The `new_str` parameter should contain the edited lines that should replace the `old_str`"""

    # 日本語訳:
    # """ファイルの表示、作成、編集のためのカスタム編集ツール
    # * 状態はコマンド呼び出しやユーザーとの対話を通じて永続的に保持されます
    # * `path`がファイルの場合、`view`は`cat -n`を適用した結果を表示します。`path`がディレクトリの場合、`view`は非表示ファイルとディレクトリを最大2階層まで一覧表示します
    # * 指定された`path`が既にファイルとして存在する場合、`create`コマンドは使用できません
    # * `command`が長い出力を生成する場合、切り詰められ`<response clipped>`とマークされます
    # * `undo_edit`コマンドは`path`のファイルに対する最後の編集を元に戻します
    # 
    # `str_replace`コマンドを使用する際の注意点:
    # * `old_str`パラメータは元のファイルから連続する1行以上と完全に一致する必要があります。空白に注意してください！
    # * `old_str`パラメータがファイル内で一意でない場合、置換は実行されません。`old_str`に十分なコンテキストを含めて一意にしてください
    # * `new_str`パラメータには`old_str`を置き換える編集済みの行を含める必要があります"""

    inputs = {
        "command": {
            "description": "The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`.",
            "type": "string",
            "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
        },
        "path": {
            "description": "Absolute path to file or directory.",
            "type": "string",
        },
        "file_text": {
            "description": "Required parameter of `create` command, with the content of the file to be created.",
            "type": "string",
            "nullable": True,
        },
        "old_str": {
            "description": "Required parameter of `str_replace` command containing the string in `path` to replace.",
            "type": "string",
            "nullable": True,
        },
        "new_str": {
            "description": "Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert.",
            "type": "string",
            "nullable": True,
        },
        "insert_line": {
            "description": "Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.",
            "type": "integer",
            "nullable": True,
        },
        "view_range": {
            "description": "Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.",
            "type": "array",
            "items": {"type": "integer"},
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self):
        super().__init__()
        self._file_history = {}

    async def forward(
        self,
        command: str,  # Literal型からstr型に変更
        path: str,
        file_text: Optional[str] = None,
        view_range: Optional[List[int]] = None,
        old_str: Optional[str] = None,
        new_str: Optional[str] = None,
        insert_line: Optional[int] = None,
    ) -> str:
        _path = Path(path)
        
        try:
            self.validate_path(command, _path)
            
            if command == "view":
                return await self.view(_path, view_range)
            elif command == "create":
                if file_text is None:
                    return "Error: Parameter `file_text` is required for command: create"
                await self.write_file(_path, file_text)
                if _path not in self._file_history:
                    self._file_history[_path] = []
                self._file_history[_path].append(file_text)
                return f"File created successfully at: {_path}"
            elif command == "str_replace":
                if old_str is None:
                    return "Error: Parameter `old_str` is required for command: str_replace"
                return await self.str_replace(_path, old_str, new_str)
            elif command == "insert":
                if insert_line is None:
                    return "Error: Parameter `insert_line` is required for command: insert"
                if new_str is None:
                    return "Error: Parameter `new_str` is required for command: insert"
                return await self.insert(_path, insert_line, new_str)
            elif command == "undo_edit":
                return await self.undo_edit(_path)
            else:
                return f'Error: Unrecognized command {command}. The allowed commands are: {", ".join(VALID_COMMANDS)}'
        except Exception as e:
            return f"Error: {str(e)}"

    def validate_path(self, command: str, path: Path):
        """
        Check that the path/command combination is valid.
        """
        # Check if its an absolute path
        if not path.is_absolute():
            suggested_path = Path("") / path
            raise ValueError(
                f"The path {path} is not an absolute path, it should start with `/`. Maybe you meant {suggested_path}?"
            )
        # Check if path exists
        if not path.exists() and command != "create":
            raise ValueError(
                f"The path {path} does not exist. Please provide a valid path."
            )
        if path.exists() and command == "create":
            raise ValueError(
                f"File already exists at: {path}. Cannot overwrite files using command `create`."
            )
        # Check if the path points to a directory
        if path.is_dir():
            if command != "view":
                raise ValueError(
                    f"The path {path} is a directory and only the `view` command can be used on directories"
                )

    async def view(self, path: Path, view_range: Optional[List[int]] = None) -> str:
        """Implement the view command"""
        if path.is_dir():
            if view_range:
                return "Error: The `view_range` parameter is not allowed when `path` points to a directory."

            # List files and directories up to 2 levels deep
            files_and_dirs = []
            for root, dirs, files in os.walk(path):
                level = root.replace(str(path), '').count(os.sep)
                if level <= 2:
                    for file in files:
                        if not file.startswith('.'):
                            files_and_dirs.append(os.path.join(root, file))
                    for dir in dirs:
                        if not dir.startswith('.'):
                            files_and_dirs.append(os.path.join(root, dir) + '/')
                if level == 2:
                    dirs[:] = []  # Don't go deeper than 2 levels
            
            output = f"Here's the files and directories up to 2 levels deep in {path}, excluding hidden items:\n"
            output += "\n".join(files_and_dirs)
            return output

        file_content = await self.read_file(path)
        init_line = 1
        if view_range:
            if len(view_range) != 2 or not all(isinstance(i, int) for i in view_range):
                return "Error: Invalid `view_range`. It should be a list of two integers."
            
            file_lines = file_content.split("\n")
            n_lines_file = len(file_lines)
            init_line, final_line = view_range
            
            if init_line < 1 or init_line > n_lines_file:
                return f"Error: Invalid `view_range`: {view_range}. Its first element `{init_line}` should be within the range of lines of the file: {[1, n_lines_file]}"
            
            if final_line > n_lines_file:
                return f"Error: Invalid `view_range`: {view_range}. Its second element `{final_line}` should be smaller than the number of lines in the file: `{n_lines_file}`"
            
            if final_line != -1 and final_line < init_line:
                return f"Error: Invalid `view_range`: {view_range}. Its second element `{final_line}` should be larger or equal than its first `{init_line}`"

            if final_line == -1:
                file_content = "\n".join(file_lines[init_line - 1:])
            else:
                file_content = "\n".join(file_lines[init_line - 1:final_line])

        return self._make_output(file_content, str(path), init_line=init_line)

    async def str_replace(self, path: Path, old_str: str, new_str: Optional[str]) -> str:
        """Implement the str_replace command, which replaces old_str with new_str in the file content"""
        # Read the file content
        file_content = (await self.read_file(path)).expandtabs()
        old_str = old_str.expandtabs()
        new_str = new_str.expandtabs() if new_str is not None else ""

        # Check if old_str is unique in the file
        occurrences = file_content.count(old_str)
        if occurrences == 0:
            return f"Error: No replacement was performed, old_str `{old_str}` did not appear verbatim in {path}."
        elif occurrences > 1:
            file_content_lines = file_content.split("\n")
            lines = [
                idx + 1
                for idx, line in enumerate(file_content_lines)
                if old_str in line
            ]
            return f"Error: No replacement was performed. Multiple occurrences of old_str `{old_str}` in lines {lines}. Please ensure it is unique"

        # Replace old_str with new_str
        new_file_content = file_content.replace(old_str, new_str)

        # Write the new content to the file
        await self.write_file(path, new_file_content)

        # Save the content to history
        if path not in self._file_history:
            self._file_history[path] = []
        self._file_history[path].append(file_content)

        # Create a snippet of the edited section
        replacement_line = file_content.split(old_str)[0].count("\n")
        start_line = max(0, replacement_line - SNIPPET_LINES)
        end_line = replacement_line + SNIPPET_LINES + new_str.count("\n")
        snippet = "\n".join(new_file_content.split("\n")[start_line:end_line + 1])

        # Prepare the success message
        success_msg = f"The file {path} has been edited. "
        success_msg += self._make_output(
            snippet, f"a snippet of {path}", start_line + 1
        )
        success_msg += "Review the changes and make sure they are as expected. Edit the file again if necessary."

        return success_msg

    async def insert(self, path: Path, insert_line: int, new_str: str) -> str:
        """Implement the insert command, which inserts new_str at the specified line in the file content."""
        file_text = (await self.read_file(path)).expandtabs()
        new_str = new_str.expandtabs()
        file_text_lines = file_text.split("\n")
        n_lines_file = len(file_text_lines)

        if insert_line < 0 or insert_line > n_lines_file:
            return f"Error: Invalid `insert_line` parameter: {insert_line}. It should be within the range of lines of the file: {[0, n_lines_file]}"

        new_str_lines = new_str.split("\n")
        new_file_text_lines = (
            file_text_lines[:insert_line]
            + new_str_lines
            + file_text_lines[insert_line:]
        )
        snippet_lines = (
            file_text_lines[max(0, insert_line - SNIPPET_LINES):insert_line]
            + new_str_lines
            + file_text_lines[insert_line:insert_line + SNIPPET_LINES]
        )

        new_file_text = "\n".join(new_file_text_lines)
        snippet = "\n".join(snippet_lines)

        await self.write_file(path, new_file_text)
        if path not in self._file_history:
            self._file_history[path] = []
        self._file_history[path].append(file_text)

        success_msg = f"The file {path} has been edited. "
        success_msg += self._make_output(
            snippet,
            "a snippet of the edited file",
            max(1, insert_line - SNIPPET_LINES + 1),
        )
        success_msg += "Review the changes and make sure they are as expected (correct indentation, no duplicate lines, etc). Edit the file again if necessary."
        return success_msg

    async def undo_edit(self, path: Path) -> str:
        """Implement the undo_edit command."""
        if path not in self._file_history or not self._file_history[path]:
            return f"Error: No edit history found for {path}."

        old_text = self._file_history[path].pop()
        await self.write_file(path, old_text)

        return f"Last edit to {path} undone successfully. {self._make_output(old_text, str(path))}"

    async def read_file(self, path: Path) -> str:
        """Read the content of a file from a given path."""
        try:
            async with aiofiles.open(path, 'r', encoding="utf-8") as file:
                return await file.read()
        except Exception as e:
            raise ValueError(f"Ran into {e} while trying to read {path}")

    async def write_file(self, path: Path, content: str) -> None:
        """Write the content of a file to a given path."""
        try:
            # Ensure the directory exists
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            async with aiofiles.open(path, 'w', encoding="utf-8") as file:
                await file.write(content)
        except Exception as e:
            raise ValueError(f"Ran into {e} while trying to write to {path}")

    def maybe_truncate(self, content: str, truncate_after: Optional[int] = MAX_RESPONSE_LEN) -> str:
        """Truncate content and append a notice if content exceeds the specified length."""
        return (
            content
            if not truncate_after or len(content) <= truncate_after
            else content[:truncate_after] + TRUNCATED_MESSAGE
        )

    def _make_output(
        self,
        file_content: str,
        file_descriptor: str,
        init_line: int = 1,
        expand_tabs: bool = True,
    ) -> str:
        """Generate output based on the content of a file."""
        file_content = self.maybe_truncate(file_content)
        if expand_tabs:
            file_content = file_content.expandtabs()
        file_content = "\n".join(
            [
                f"{i + init_line:6}\t{line}"
                for i, line in enumerate(file_content.split("\n"))
            ]
        )
        return (
            f"Here's the result of running `cat -n` on {file_descriptor}:\n"
            + file_content
            + "\n"
        )
