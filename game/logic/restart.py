# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Application restart helper for LunArk: Genesis.

Pure Python logic for constructing restart command lists without Pygame dependencies.
"""

from pathlib import Path
import sys
from typing import Sequence


def build_restart_command(
    executable: str | None = None,
    argv: Sequence[str] | None = None,
    flag: str = "--skip-startup",
) -> list[str]:
    """Construct a command list to restart the application as a new process.

    Returns a list consisting of:
    1. The Python executable path.
    2. The absolute path of the entry script (from argv[0], falling back to main.py).
    3. Any additional arguments from argv, preserving order without duplicates.
    4. The --skip-startup flag (appended if not already present).

    Args:
        executable: Python interpreter binary path. Defaults to sys.executable.
        argv: Command-line arguments sequence. Defaults to sys.argv.
        flag: Fast-boot flag to pass to the new process. Defaults to '--skip-startup'.

    Returns:
        list[str]: Command arguments list suitable for subprocess.Popen.
    """
    python_bin = executable or sys.executable
    raw_argv = list(argv if argv is not None else sys.argv)

    if raw_argv and raw_argv[0]:
        script_path = str(Path(raw_argv[0]).resolve())
        extra_args = raw_argv[1:]
    else:
        script_path = str(Path("main.py").resolve())
        extra_args = []

    cmd: list[str] = [python_bin, script_path]

    # Add other arguments without duplicates, excluding the target flag
    seen: set[str] = set()
    for arg in extra_args:
        if arg != flag and arg not in seen:
            cmd.append(arg)
            seen.add(arg)

    # Always ensure the flag is appended at the end
    cmd.append(flag)

    return cmd
