# claude-chat-cli

A tiny terminal **chat** with Claude — back-and-forth like Claude.ai, but in your
shell. It uses your existing **Claude Code subscription auth**, so **no API key
is required**.

It wraps the `claude` CLI in print mode and strips it down to a plain
conversational assistant: tools are disabled and the coding/agent system prompt
is replaced, so it answers like a chat, not a coding agent.

## Requirements

- Python 3 (standard library only — no dependencies)
- The [`claude`](https://docs.claude.com/en/docs/claude-code) CLI installed, on
  your `PATH`, and already logged in (`claude` once interactively if needed)

## Usage

```bash
python3 chat.py
```

Then just talk:

```
claude-chat — type 'exit' or 'quit' (or Ctrl-D) to leave.

you> my name is Tyler and I like teal
Hi Tyler! Nice to meet you. Teal's a great choice.

you> what's my favorite color?
Teal.

you> exit
bye.
```

Pick a model for the session:

```bash
python3 chat.py --model opus     # or sonnet, haiku
```

Leave with `exit`, `quit`, Ctrl-D, or Ctrl-C.

## How it works

- One UUID is generated per session. Turn 1 uses `claude -p --session-id <uuid>`;
  later turns use `--resume <uuid>`, which is what preserves conversation memory.
- Every call adds `--system-prompt "<conversational persona>"`, `--tools ""`
  (no tools), and `--output-format json` (the reply is read from `.result`).
- Conversation memory lasts only for the life of one REPL session — nothing is
  resumed across launches.

## Security

- **Refuses to run as root** — exits immediately if `geteuid() == 0`.
- **No shell injection** — the `claude` subprocess is always invoked with an
  argument list (never `shell=True`); your input is passed as a single argument
  and can't be interpreted as flags or shell metacharacters.
- **No tools** — `--tools ""` means the session has no file, bash, or network
  access. Even a confused reply can't touch your system.
- **No secrets handled or stored** — it relies entirely on your existing Claude
  Code auth, never reads/prints/persists API keys, and doesn't log conversation
  text to disk.
- **Neutral working directory** — runs from a temp dir so no project `CLAUDE.md`
  is pulled into the prompt.

## Limitations (by design)

- Interactive REPL only (no one-shot/pipe mode).
- No streaming output — each turn shows a `…thinking` indicator, then the reply.
- No cross-session persistence.
