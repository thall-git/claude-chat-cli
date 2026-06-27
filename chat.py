#!/usr/bin/env python3
"""claude-chat — a plain-chat REPL on top of the Claude Code CLI.

Talk to Claude in the terminal using your existing Claude Code subscription
auth. No API key required. Tools are disabled and the agent/coding system
prompt is replaced with a conversational persona, so this behaves like a chat,
not a coding agent.

Conversation memory lasts for the life of one REPL session only.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import uuid

PERSONA = (
    "You are a helpful, friendly conversational assistant chatting with the "
    "user in a terminal. Reply naturally and concisely in plain text. You have "
    "no access to tools, files, or the system."
)

EXIT_WORDS = {"exit", "quit"}


def refuse_root():
    """Refuse to run as root. Degrades gracefully where geteuid is absent."""
    geteuid = getattr(os, "geteuid", None)
    if geteuid is not None and geteuid() == 0:
        sys.stderr.write("claude-chat: refusing to run as root.\n")
        sys.exit(1)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="chat.py",
        description="Plain-chat REPL backed by the Claude Code CLI (no API key).",
    )
    parser.add_argument(
        "--model",
        help="Model alias to pass through to claude (e.g. opus, sonnet, haiku). "
        "Defaults to your normal model.",
    )
    return parser.parse_args(argv)


def build_base_cmd(model):
    """Build the invariant part of the claude command (no shell, argv list)."""
    cmd = [
        "claude",
        "-p",
        "--output-format",
        "json",
        "--tools",
        "",  # disable ALL built-in tools: no file/bash/network access
        "--system-prompt",
        PERSONA,
    ]
    if model:
        cmd += ["--model", model]
    return cmd


def ask(base_cmd, session_id, prompt, first_turn, cwd):
    """Run one turn against the claude CLI and return the reply text.

    Raises RuntimeError with a human-readable message on any failure.
    """
    cmd = list(base_cmd)
    cmd += ["--session-id", session_id] if first_turn else ["--resume", session_id]
    cmd.append(prompt)  # user input is a single argv element — never shell-parsed

    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError:
        raise RuntimeError("the 'claude' CLI was not found on your PATH.")

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(detail or f"claude exited with code {proc.returncode}.")

    try:
        data = json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        raise RuntimeError((proc.stdout or proc.stderr or "no output").strip())

    if data.get("is_error"):
        raise RuntimeError(
            str(data.get("result") or data.get("api_error_status") or "claude reported an error.")
        )

    return data.get("result", "")


def repl(args):
    session_id = str(uuid.uuid4())
    base_cmd = build_base_cmd(args.model)
    cwd = tempfile.gettempdir()  # neutral cwd: no project CLAUDE.md pulled in
    first_turn = True

    print("claude-chat — type 'exit' or 'quit' (or Ctrl-D) to leave.\n")

    while True:
        try:
            prompt = input("you> ")
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            break

        prompt = prompt.strip()
        if not prompt:
            continue
        if prompt.lower() in EXIT_WORDS:
            break

        sys.stdout.write("…thinking\r")
        sys.stdout.flush()
        try:
            reply = ask(base_cmd, session_id, prompt, first_turn, cwd)
            first_turn = False  # only advance on success, so resume stays valid
        except RuntimeError as err:
            sys.stdout.write(" " * 12 + "\r")  # clear the thinking line
            print(f"[error] {err}\n", file=sys.stderr)
            continue

        sys.stdout.write(" " * 12 + "\r")  # clear the thinking line
        print(f"{reply}\n")

    print("bye.")


def main(argv=None):
    refuse_root()
    args = parse_args(argv)
    repl(args)


if __name__ == "__main__":
    main()
