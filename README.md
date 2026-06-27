# claude-chat-cli

A tiny terminal **chat** with Claude — back-and-forth like Claude.ai, but in your
shell. It uses your existing **Claude Code subscription auth**, so **no API key
is required**.

It wraps the `claude` CLI in print mode and strips it down to a plain
conversational assistant: tools are disabled and the coding/agent system prompt
is replaced, so it answers like a chat, not a coding agent.

## Requirements

- **A Claude subscription** (Pro/Max or a Claude account with Claude Code
  access). This tool uses that subscription for auth — it does **not** use an
  API key.
- **Claude Code installed and configured.** The
  [`claude`](https://docs.claude.com/en/docs/claude-code) CLI must be installed,
  on your `PATH`, and already signed in (run `claude` once interactively to log
  in if you haven't).
- Python 3 (standard library only — no dependencies).

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

Defaults to **opus**. Pick a different model for the session:

```bash
python3 chat.py --model sonnet   # or haiku, opus
```

Leave with `exit`, `quit`, Ctrl-D, or Ctrl-C.

## How it works

- One UUID is generated per session. Turn 1 uses `claude -p --session-id <uuid>`;
  later turns use `--resume <uuid>`, which is what preserves conversation memory.
- Every call adds `--system-prompt "<conversational persona>"` and `--tools ""`
  (no tools).
- Replies **stream live**: the call uses
  `--output-format stream-json --include-partial-messages`, and each text delta
  is printed token-by-token as it arrives.
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
- No cross-session persistence.

## License

[MIT](LICENSE) — open source. Do whatever you like.
