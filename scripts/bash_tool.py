import asyncio
import os
from typing import Optional

from smolagents import Tool


_BASH_DESCRIPTION = """Execute a bash command in the terminal.
* Long running commands: For commands that may run indefinitely, it should be run in the background and the output should be redirected to a file, e.g. command = `python3 app.py > server.log 2>&1 &`.
* Interactive: If a bash command returns exit code `-1`, this means the process is not yet finished. The assistant must then send a second call to terminal with an empty `command` (which will retrieve any additional logs), or it can send additional text (set `command` to the text) to STDIN of the running process, or it can send command=`ctrl+c` to interrupt the process.
* Timeout: If a command execution result says "Command timed out. Sending SIGINT to the process", the assistant should retry running the command in the background.
"""

# 日本語訳:
# """ターミナルでbashコマンドを実行します。
# * 長時間実行コマンド: 無期限に実行される可能性のあるコマンドは、バックグラウンドで実行し、出力をファイルにリダイレクトする必要があります。例: command = `python3 app.py > server.log 2>&1 &`
# * インタラクティブ: bashコマンドが終了コード `-1` を返す場合、プロセスがまだ終了していないことを意味します。アシスタントは空の `command` でターミナルに2回目の呼び出しを送信するか（追加のログを取得するため）、追加のテキストを送信するか（`command` にテキストを設定して実行中のプロセスのSTDINに送信）、または command=`ctrl+c` を送信してプロセスを中断することができます。
# * タイムアウト: コマンド実行結果が「Command timed out. Sending SIGINT to the process」と表示された場合、アシスタントはコマンドをバックグラウンドで再実行する必要があります。
# """


class _BashSession:
    """A session of a bash shell."""

    _started: bool
    _process: asyncio.subprocess.Process

    command: str = "/bin/bash"
    _output_delay: float = 0.2  # seconds
    _timeout: float = 120.0  # seconds
    _sentinel: str = "<<exit>>"

    def __init__(self):
        self._started = False
        self._timed_out = False

    async def start(self):
        if self._started:
            return

        self._process = await asyncio.create_subprocess_shell(
            self.command,
            preexec_fn=os.setsid,
            shell=True,
            bufsize=0,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._started = True

    def stop(self):
        """Terminate the bash shell."""
        if not self._started:
            raise Exception("Session has not started.")
        if self._process.returncode is not None:
            return
        self._process.terminate()

    async def run(self, command: str):
        """Execute a command in the bash shell."""
        if not self._started:
            raise Exception("Session has not started.")
        if self._process.returncode is not None:
            return {
                "system": "tool must be restarted",
                "error": f"bash has exited with returncode {self._process.returncode}",
            }
        if self._timed_out:
            raise Exception(
                f"timed out: bash has not returned in {self._timeout} seconds and must be restarted",
            )

        # we know these are not None because we created the process with PIPEs
        assert self._process.stdin
        assert self._process.stdout
        assert self._process.stderr

        # send command to the process
        self._process.stdin.write(
            command.encode() + f"; echo '{self._sentinel}'\n".encode()
        )
        await self._process.stdin.drain()

        # read output from the process, until the sentinel is found
        try:
            async with asyncio.timeout(self._timeout):
                while True:
                    await asyncio.sleep(self._output_delay)
                    # if we read directly from stdout/stderr, it will wait forever for
                    # EOF. use the StreamReader buffer directly instead.
                    output = (
                        self._process.stdout._buffer.decode()
                    )  # pyright: ignore[reportAttributeAccessIssue]
                    if self._sentinel in output:
                        # strip the sentinel and break
                        output = output[: output.index(self._sentinel)]
                        break
        except asyncio.TimeoutError:
            self._timed_out = True
            raise Exception(
                f"timed out: bash has not returned in {self._timeout} seconds and must be restarted",
            ) from None

        if output.endswith("\n"):
            output = output[:-1]

        error = (
            self._process.stderr._buffer.decode()
        )  # pyright: ignore[reportAttributeAccessIssue]
        if error.endswith("\n"):
            error = error[:-1]

        # clear the buffers so that the next output can be read correctly
        self._process.stdout._buffer.clear()  # pyright: ignore[reportAttributeAccessIssue]
        self._process.stderr._buffer.clear()  # pyright: ignore[reportAttributeAccessIssue]

        return {"output": output, "error": error}


class BashTool(Tool):
    """A tool for executing bash commands"""

    name = "bash"
    description = _BASH_DESCRIPTION
    inputs = {
        "command": {
            "description": "The bash command to execute. Can be empty to view additional logs when previous exit code is `-1`. Can be `ctrl+c` to interrupt the currently running process.",
            "type": "string",
        },
        "restart": {
            "description": "[Optional]: Whether to restart the bash session. Default is False.",
            "type": "boolean",
            "nullable": True,
        },
    }
    output_type = "object"

    _session: Optional[_BashSession] = None

    async def forward(self, command: str, restart: Optional[bool] = False) -> dict:
        if restart:
            if self._session:
                self._session.stop()
            self._session = _BashSession()
            await self._session.start()

            return {"system": "tool has been restarted"}

        if self._session is None:
            self._session = _BashSession()
            await self._session.start()

        if command:
            return await self._session.run(command)

        raise Exception("no command provided.")


if __name__ == "__main__":
    bash = BashTool()
    rst = asyncio.run(bash.forward("ls -l"))
    print(rst)