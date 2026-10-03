# Exercises

Do them in order. Each one says which [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) lesson covers the same idea in more depth.

| # | Exercise | You'll learn | Time | Upstream |
|---|---|---|---|---|
| 00 | [Setup check](00-setup-check/) | Everything is wired up | 10 min | |
| 01 | [Inspect traffic and tokens](01-inspect-traffic-and-tokens/) | What actually goes over the wire, and what it costs | 15 min | s01 |
| 02 | [Add a tool loop](02-add-a-tool-loop/) | The agent loop: `tool_use` → run → `tool_result` → repeat | 20 min | s01 |
| 03 | [File system access](03-filesystem-access/) | A tool table, file tools, sandboxing paths | 20 min | s02 |
| 04 | [Permissions and hooks](04-permissions-and-hooks/) | Who decides what the agent may run | stretch | s03, s04 |
| 05 | [Watch the context grow](05-watch-the-context-grow/) | Why long sessions get slow and expensive, and compaction | stretch | s08 |
| 06 | [Go further](06-go-further/) | Todo lists, subagents, skills, MCP | at home | s05–s07, s14 |

**How to run a starter** (always from the repo root, so `.env` is found):

```bash
uv run --project agent python exercises/02-add-a-tool-loop/starter.py
```

Stuck? The solution to each exercise is the next file in [`agent/`](../agent/). Try for ten minutes before you peek.

**Keep the proxy open the whole time.** Every exercise is easier when you can see the requests.
