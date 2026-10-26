"""
Lab 1.2 — Tool 2: Sandboxed Code Executor
==========================================

Implement one function: exec_python.

The executor must run an arbitrary Python script in a child process —
NOT via exec() or eval() — so that:
  - Infinite loops are killed after the timeout.
  - Crashes in the script do not crash the agent process.
  - The agent always receives useful output regardless of outcome.

Run the tests to verify your implementation before moving to agent.py:
  pytest tests/test_code_executor.py -v

Success criterion (from the lab spec):
  The agent writes a Python file, executes it, reads the output, and
  reports the result — all in one agentic loop.
"""

import os
import subprocess
import sys

MAX_OUTPUT_CHARS = 2000
MAX_TIMEOUT = 30


def exec_python(path: str, timeout: int = 10) -> str:
    """
    Execute a Python script in a sandboxed subprocess.

    Parameters
    ----------
    path : str
        Path to the .py file to execute. Must exist before calling this.
    timeout : int
        Maximum seconds to allow. Values above MAX_TIMEOUT (30) are
        clamped silently. Defaults to 10.

    Returns
    -------
    str
        Success  : stdout, truncated to MAX_OUTPUT_CHARS with a
                   "[output truncated]" suffix if it was cut.
        Timeout  : a message naming the script and stating it was killed.
        Non-zero : stderr and the return code, both in the returned string.
        Any other error : a descriptive string — do NOT raise.

    Hints
    -----
    Clamp the timeout first:
        effective_timeout = min(timeout, MAX_TIMEOUT)

    Use subprocess.run with these arguments:
        [sys.executable, path]   ← same Python env as the agent
        capture_output=True      ← captures stdout and stderr separately
        text=True                ← returns str instead of bytes
        timeout=effective_timeout

    Catch subprocess.TimeoutExpired to handle infinite loops.
    The exception exposes a .timeout attribute you can include in the
    message.

    Truncate long output:
        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + "\\n[output truncated]"

    Wrap the ENTIRE body in try/except Exception as e as a last-resort
    safety net — this function must never propagate an exception to the
    agent loop.

    Example return values
    ---------------------
    Success : "hello from subprocess\\n"
    Timeout : "Error: script 'loop.py' exceeded timeout of 2s and was killed."
    Crash   : "Error (exit code 1):\\nTraceback (most recent call last):\\n  ..."
    """
    try:
        effective_timeout = min(timeout, MAX_TIMEOUT)

        if not path or not os.path.isfile(path):
            return f"Error: script '{path}' does not exist or is not a file."

        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=effective_timeout,
        )

        if result.returncode != 0:
            return _truncate(f"Error (exit code {result.returncode}):\n{result.stderr}")

        # An empty string would read like a failure to the agent
        if not result.stdout:
            return "Script ran successfully with no output."
        return _truncate(result.stdout)

    except subprocess.TimeoutExpired as e:
        return f"Error: script '{path}' exceeded timeout of {e.timeout}s and was killed."
    except Exception as e:
        return f"Error executing script '{path}': {e}"


def _truncate(output: str) -> str:
    if len(output) > MAX_OUTPUT_CHARS:
        output = output[:MAX_OUTPUT_CHARS] + "\n[output truncated]"
    return output
