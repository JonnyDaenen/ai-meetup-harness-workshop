# 06: Go further

You now have the core of every coding agent: a loop, tools, permissions and context management. Everything else is variations on those. Good next steps in [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code), with what to look for in the proxy:

| Lesson | Idea | What to watch in the proxy |
|---|---|---|
| [s05 TodoWrite](https://github.com/shareAI-lab/learn-claude-code/tree/main/s05_todo_write) | The model writes a plan as a tool call, and the harness reminds it of the plan | The todo list reappearing in later requests |
| [s06 Subagent](https://github.com/shareAI-lab/learn-claude-code/tree/main/s06_subagent) | A child agent with a fresh `messages[]`; only its summary comes back | Two separate conversations, and a small result in the parent |
| [s07 Skill Loading](https://github.com/shareAI-lab/learn-claude-code/tree/main/s07_skill_loading) | Only names and descriptions go in the prompt; the full text is loaded on demand | The skills list in Claude Code's `<system-reminder>` |
| [s14 MCP Plugin](https://github.com/shareAI-lab/learn-claude-code/tree/main/s14_mcp_plugin) | Tools discovered from an external server and namespaced | `mcp__server__tool` names in `tools` |

Further:
- Point Claude Code at your local model ([docs/claude-code.md](../../docs/claude-code.md)) and compare its traffic with J5's.
- [shareAI-lab/claw0](https://github.com/shareAI-lab/claw0): always-on agents (heartbeat, cron, chat integrations).
- Give J5 an MCP client, so it can use the same tool servers as Claude Code.
