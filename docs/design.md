# claude-chat — CLI chat REPL (design)

Date: 2026-06-27

## Purpose

A terminal chat with Claude, back-and-forth like Claude.ai, using the existing
Claude Code subscription auth — **no API key required**. It wraps the `claude`
CLI in `-p` (print) mode rather than calling the Anthropic API directly.

The goal is a *plain chat* experience, not a coding agent: tools are disabled
and the coding/agent system prompt is replaced with a conversational persona.

## Non-goals (YAGNI)

- No cross-launch persistence — conversation memory lasts only for the life of a
  single REPL session.
- No streaming token output — each turn is a single request with a "thinking"
  indicator. Chat replies are short enough that this is fine.
- No third-party dependencies — Python standard library only.
- No agent tools (file/bash/web access). This is chat, not Claude Code.

## How it works

A single Python file, `chat.py`, runs a read-eval-print loop:

1. On launch, generate one UUID for the session (`uuid.uuid4()`).
2. Read a line of input from the user.
3. Shell out to the `claude` CLI as a subprocess and print the reply.
4. Repeat until the user exits.

### Session continuity

Memory across turns is achieved with the CLI's own session store:

- **Turn 1:** `claude -p --session-id <uuid> ...` — creates the session.
- **Turn 2+:** `claude -p --resume <uuid> ...` — resumes it, preserving history.

Verified during design: turn 2 correctly recalled a fact stated in turn 1.

### Plain-chat behavior

Every subprocess call includes:

- `--system-prompt "<conversational persona>"` — fully replaces Claude Code's
  default agent/coding system prompt.
- `--tools ""` — disables all built-in tools, so there is no file/bash access
  and no permission prompts.
- `--output-format json` — returns a JSON object; the script parses `.result`
  for the reply text. (`.session_id` and `.is_error` are also available.)

The subprocess is run from a neutral working directory (e.g. the user's home or
a temp dir) so no project `CLAUDE.md` is auto-discovered into the context.

Auth note: plain `claude -p` uses the user's OAuth/subscription credentials.
`--bare` is deliberately **not** used because it forces `ANTHROPIC_API_KEY`
auth, which would defeat the no-API-key requirement.

## Security

Security controls, in order of importance:

- **Refuse to run as root.** At startup, if `os.geteuid() == 0`, print an error
  and exit non-zero before doing anything else. There is no reason to chat as
  root, and it avoids writing session state into root-owned paths. (Guarded so
  it degrades gracefully on platforms lacking `geteuid`.)
- **No shell, no injection.** The subprocess is always invoked with an argument
  **list** via `subprocess.run([...])` — never a shell string and never
  `shell=True`. User input is passed as a single argv element, so it cannot be
  interpreted as flags or shell metacharacters.
- **Tools disabled as a hard boundary.** `--tools ""` means the wrapped Claude
  session has no file, bash, or network tool access. Even a hostile/confused
  reply cannot touch the filesystem or run commands. This is the primary blast-
  radius control.
- **No secrets handled or stored.** The script never reads, prints, or persists
  API keys — it relies entirely on the existing Claude Code subscription auth.
  Conversation text is not logged to disk; it lives only in the CLI's own
  session store under the user's home, written with that user's permissions.
- **No untrusted context loaded.** Running from a neutral cwd prevents an
  unexpected project `CLAUDE.md` from being pulled into the system prompt.
- **Fail closed.** A failed turn never silently downgrades security (tools stay
  off, prompt stays replaced); it just reports the error and continues.

## Command-line interface

```
chat.py [--model <alias>]
```

- `--model` (optional): passthrough to `claude --model` (e.g. `opus`, `sonnet`,
  `haiku`). Omitted by default, so the user's normal model is used.

## REPL UX

- **First, refuse to run as root** (see Security), then parse args.
- Prompt the user with a simple marker (e.g. `you> `).
- While waiting on the subprocess, print a `…thinking` indicator, cleared once
  the reply arrives.
- Print Claude's reply, then loop.
- Exit cleanly on `exit`, `quit`, Ctrl-D (EOF), or Ctrl-C.
- Blank / whitespace-only input is ignored (no API call).

## Error handling

The REPL must survive a failed turn rather than crashing:

- Subprocess non-zero exit, or `is_error: true` in the JSON → print a short
  error line (including stderr if useful) and stay in the loop.
- JSON that fails to parse → print the raw stderr/stdout and continue.
- The session UUID is unchanged by a failed turn, so the next turn still
  resumes correctly.

## Components

| Unit | Responsibility |
|------|----------------|
| startup guard | refuse to run as root (`os.geteuid`) before anything else |
| arg parsing | read optional `--model`; build base CLI args |
| `ask(prompt, first_turn)` | run the subprocess for one turn, return reply text or raise a clear error |
| REPL loop | read input, manage first-vs-resume, render thinking indicator, handle exit/errors |

`ask()` is the single integration point with the `claude` CLI and can be tested
in isolation by stubbing the subprocess call.

## Location

New project directory in the repo: `claude-chat/` containing `chat.py` and a
`README.md` (purpose, usage, the no-API-key/subscription note, and the design
rationale), per the per-project convention.
